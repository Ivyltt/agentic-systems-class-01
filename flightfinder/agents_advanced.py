"""Multi-agent collaboration layer for FlightFinder Pro.

The team has three roles: merge/rank candidates, critique against user constraints, and summarize into a structured report. The design leaves one meaningful routing decision to the model while deterministic rules preserve workflow completion and retry limits."""

import os
from typing import List, Optional, Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, SourceMatchTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, StructuredMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from schemas import FlightSearchReport, ParsedQuery

MAX_CRITIC_RETRIES = 1




# This prompt defines the only model-controlled speaker-routing decision in the team.
SELECTOR_PROMPT = """You are the dispatcher for a multi-agent workflow. Decide which role should speak next.

Available roles and responsibilities:
{roles}

Conversation history:
{history}

Decision rules:
- If the merge/ranking agent just produced candidate flights, decide whether critic review is needed:
  * If the user explicitly mentioned a budget, cabin requirement, or other concrete preference, choose budget_critic_agent so it can verify the candidates.
  * If the user gave no budget, cabin, or preference, choose summarizer_agent directly and do not waste an extra round.
- If the critic agent just spoke, follow its verdict: choose merge_ranker_agent when it requests reranking, and choose summarizer_agent when it approves or reports no data.

Choose the next speaker from {participants}. Return only the role name, with no extra text."""


def build_model_client() -> OpenAIChatCompletionClient:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY was not found. Copy .env.example to .env and fill in your key, "
            "or export OPENAI_API_KEY before running."
        )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAIChatCompletionClient(model=model, api_key=api_key)


def build_query_parser_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Create the agent that converts the user's request into ParsedQuery."""
    return AssistantAgent(
        name="query_parser_agent",
        model_client=model_client,
        description="Parse the user's natural-language flight request into structured parameters",
        output_content_type=ParsedQuery,
        system_message="""Parse the user's flight request into structured fields.

The user message includes today's date. If the user gives a relative or incomplete date such as "next Tuesday" or "November 5", convert it into an absolute YYYY-MM-DD date using today's date as the reference. Leave omitted fields such as budget and cabin as null. Do not guess.

The date field is the user's preferred date when one is stated. For a date range, use the first day as date unless the user identifies a preferred day inside the range.

For date_is_flexible, judge the wording semantically rather than by simple keyword matching. Vague wording such as "around November 5", "early November", or an explicit range means true unless the user insists on an exact date. Wording such as "must be", "only", or "cannot change" means false.

When date_is_flexible is true, always fill date_window_start and date_window_end with the earliest and latest acceptable departure dates. Interpret "around DATE" as one day before through one day after, "early MONTH" as days 1 through 7, "mid MONTH" as days 10 through 20, and "late MONTH" as days 21 through the last day. For an explicit range, preserve its endpoints. When the date is exact, set both window fields to null.""",
    )


def build_merge_ranker_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    return AssistantAgent(
        name="merge_ranker_agent",
        model_client=model_client,
        description=(
            "Merge/ranking agent: deduplicate and rank candidate flights from parallel searches. "
            "It speaks first after search results, and handles reranking if the critic asks for it."
        ),
        system_message="""You are the merge/ranking agent.

You will see candidate flights from one or more parallel date searches, plus user preferences such as budget and cabin. Each strategy names the departure date it searched.

Merge and deduplicate the results. Rank up to 5 candidate flights by value, balancing price and duration while prioritizing user budget/cabin preferences. Label which strategy produced each flight.

If the conversation history contains critic feedback requesting looser criteria, rerank accordingly. For example, if the critic says to relax the budget to $X, include options that were previously excluded for exceeding the original budget.

If every search path failed or returned no real flight data, state that no usable candidate flights are available. Do not invent flight information.

Never drop a flight for being over the user's budget, and never say that no usable candidates are available when the results above list real flights. Whether the list meets the budget is the critic's call, not yours.

Output only the candidate list. Do not make the final budget-satisfaction judgment; that belongs to the critic agent.""",
    )


def build_budget_critic_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    return AssistantAgent(
        name="budget_critic_agent",
        model_client=model_client,
        description=(
            "Critic agent: checks whether candidates satisfy the user's budget/preferences and decides "
            "whether reranking is needed or the list can be finalized."
        ),
        system_message="""You are the critic agent. Your job is final quality control before candidate flights are shown to the user.

Inspect the merge/ranking agent's candidate list. Your reply must begin with exactly one of these three words, uppercase and at the start of the message:

- NO_DATA - The list is empty, or the content shows a fetch error or no real flight data. Do not request reranking when the source data is missing.
- RETRY - The user mentioned a budget, cabin, or other preference, but none of the candidates satisfy it, and you have not already said RETRY in this conversation. Explain which condition should be relaxed, such as "relax the budget to $X" or "allow one stop".
- APPROVED - The candidates satisfy the user's preferences, or they still do not fully satisfy them after one retry. In the latter case, approve and honestly explain that these are the closest options found.

If the user did not mention any budget or cabin preference, APPROVED is fine.

The first word must be NO_DATA, RETRY, or APPROVED. Do not add a prefix, Markdown decoration, or a friendly lead-in before that word.""",
    )


def build_summarizer_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Create the final agent that returns FlightSearchReport."""
    return AssistantAgent(
        name="summarizer_agent",
        model_client=model_client,
        description=(
            "Summarizer agent: turns confirmed candidate flights into the final structured report. "
            "It is the last step of the workflow."
        ),
        output_content_type=FlightSearchReport,
        system_message="""Create the final structured report from the merge/ranking agent's candidates and the critic's verdict, if any.

- If the critic said NO_DATA, or if the candidate list contains no real flights, set options to an empty list, set within_budget to false, and explain in notes that fetching failed or no real flight data was available. Do not invent flights.
- Otherwise, fill options with up to 5 candidate flights. Copy each strategy's searched date into the option's departure_date field, and preserve the dated source_strategy label so date-window results remain distinguishable. Set within_budget according to the critic verdict; if no critic was used, judge from the candidates and the user's budget yourself. Add one or two helpful notes, such as whether the budget was relaxed or another date in the window is better.""",
    )


def _critic_verdict(content: object) -> str:
    """Normalize the critic's first word into a routing signal."""
    if not isinstance(content, str):
        return "APPROVED"

    head = content.strip().lstrip("#*_`>-~\"'“”‘’ \t\r\n")[:40].upper()
    for verdict in ("NO_DATA", "RETRY", "APPROVED"):
        if head.startswith(verdict):
            return verdict
    return "APPROVED"


def make_selector_func():
    """Return deterministic routing rules around the model-controlled selection point."""

    def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> Optional[str]:
        if not messages:
            return "merge_ranker_agent"

        last = messages[-1]
        source = getattr(last, "source", None)

        if source in (None, "user"):
            return "merge_ranker_agent"

        if source == "merge_ranker_agent":

            previous_source = getattr(messages[-2], "source", None) if len(messages) >= 2 else None
            if previous_source == "merge_ranker_agent":
                critic_spoke = any(
                    getattr(m, "source", None) == "budget_critic_agent" for m in messages
                )
                return "summarizer_agent" if critic_spoke else "budget_critic_agent"


            return None

        if source == "budget_critic_agent":
            critic_turns = sum(
                1 for m in messages if getattr(m, "source", None) == "budget_critic_agent"
            )
            verdict = _critic_verdict(getattr(last, "content", ""))

            if verdict == "RETRY" and critic_turns <= MAX_CRITIC_RETRIES:
                return "merge_ranker_agent"
            return "summarizer_agent"


        return None

    return selector_func


def make_candidate_func():
    """Return candidate speaker lists that guide SelectorGroupChat choices."""

    def candidate_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> List[str]:
        if not messages:
            return ["merge_ranker_agent"]

        last = messages[-1]
        source = getattr(last, "source", None)

        if source == "merge_ranker_agent":
            return ["budget_critic_agent", "summarizer_agent"]


        if source == "budget_critic_agent":
            return ["merge_ranker_agent", "summarizer_agent"]
        if source == "summarizer_agent":
            return ["summarizer_agent"]
        return ["merge_ranker_agent"]

    return candidate_func


# The team combines model judgment with deterministic safeguards for completion.
def build_advanced_team(model_client: OpenAIChatCompletionClient) -> SelectorGroupChat:
    merge_ranker_agent = build_merge_ranker_agent(model_client)
    budget_critic_agent = build_budget_critic_agent(model_client)
    summarizer_agent = build_summarizer_agent(model_client)


    termination = SourceMatchTermination(["summarizer_agent"]) | MaxMessageTermination(12)

    return SelectorGroupChat(
        [merge_ranker_agent, budget_critic_agent, summarizer_agent],
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=SELECTOR_PROMPT,
        selector_func=make_selector_func(),
        candidate_func=make_candidate_func(),

        allow_repeated_speaker=True,

        custom_message_types=[StructuredMessage[FlightSearchReport]],
    )
