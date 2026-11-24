"""Prompt caching demo: one scenario per way of using cache_control.

    python cache_demo.py              # run every scenario
    python cache_demo.py tools ttl    # run only the named ones

Scenarios: automatic, manual, ttl, tools, conversation, shared_prefix, multi
Study guide with concepts and exercises: docs/claude-concepts-guide.html (Caching tab).

Credentials and the gateway URL come from the environment (ANTHROPIC_AUTH_TOKEN
or ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL), so nothing secret lives in this file.
"""
import inspect
import os
import sys
import textwrap
import uuid

import anthropic

# Cheapest current model by default. ANTHROPIC_MODEL overrides it.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5")

# DEMO ONLY: a random id at the very start of every prefix, so each run starts
# with a cold cache and shows a write first. In production you want the
# opposite: a prefix that is byte-identical across requests.
RUN_ID = uuid.uuid4().hex[:8]

EPHEMERAL = {"type": "ephemeral"}  # 5-minute lifetime, refreshed on every read

KEY_FACTS = {
    7: "Refunds are accepted within 30 days of purchase with a receipt.",
    12: "Passwords must be rotated every 90 days.",
    31: "Laptops are replaced every 4 years.",
    48: "Remote work requires manager approval and a signed agreement.",
}

QUESTIONS = [
    "How many days do customers have to request a refund?",
    "How often must passwords be rotated?",
    "How often are laptops replaced?",
]


def build_handbook(title: str) -> str:
    """A long, deterministic document (about 7K tokens)."""
    sections = []
    for n in range(1, 61):
        fact = KEY_FACTS.get(n, "No special rules apply to this section.")
        sections.append(
            f"Section {n}. Policy area {n}. {fact} "
            f"Employees in area {n} must follow the standard review process, "
            f"record decisions in the shared log, and escalate exceptions to the "
            f"area {n} lead within five working days. Documentation for area {n} "
            f"is reviewed once per quarter, and any change needs two approvals "
            f"before it takes effect. Training for area {n} is repeated every year."
        )
    return f"{title} [run {RUN_ID}]\n\n" + "\n\n".join(sections)


def build_tools(title: str) -> list[dict]:
    """12 tools with long descriptions, so the tool block is big enough to cache."""
    tools = []
    for n in range(1, 13):
        description = (
            f"Look up the official policy for area {n}. Use this when the user asks "
            f"about rules, deadlines, approvals or escalation in area {n}. "
            "Returns the policy text, the date it was last reviewed, and the owner. "
            "Do not use it for questions about other areas. "
        ) * 4
        if n == 1:
            description = f"[{title} run {RUN_ID}] " + description
        tools.append(
            {
                "name": f"lookup_area_{n}",
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": {"topic": {"type": "string"}},
                    "required": ["topic"],
                },
            }
        )
    return tools


def send(client: anthropic.Anthropic, label: str, question: str, **request):
    """Send one request and print how its input tokens were billed."""
    response = client.messages.create(model=MODEL, max_tokens=300, **request)
    text = next((b.text for b in response.content if b.type == "text"), "(tool call)")
    usage = response.usage
    print(f"  {label}")
    print(f"    Q: {question}")
    print(f"    A: {text.strip()[:90]}")
    print(
        f"    WRITE {usage.cache_creation_input_tokens or 0:>6}   "
        f"READ {usage.cache_read_input_tokens or 0:>6}   "
        f"normal {usage.input_tokens or 0:>6}"
    )
    return response


def user(question: str) -> list[dict]:
    return [{"role": "user", "content": question}]


# Each scenario's docstring is printed before it runs.
# EXPECT is the textbook behavior; real results can differ (see the HTML guide).

def automatic(client):
    """AUTOMATIC: one top-level cache_control, the API picks the block.

    WHAT   cache_control goes on the request itself, not on a content block.
           The API caches the last cacheable block for you.
    WHEN   You want caching with the least code and no fine placement.
    EXPECT call 1 = WRITE, call 2 = READ.
    """
    doc = build_handbook("Handbook (automatic)")
    for i, q in enumerate(QUESTIONS[:2]):
        send(client, f"call {i + 1}", q,
             cache_control=EPHEMERAL,  # caches the last cacheable block
             system=doc, messages=user(q))


def manual(client):
    """MANUAL: you mark the exact block that ends the cached prefix.

    WHAT   cache_control sits on one block (here the system prompt).
           Everything up to and including that block is cached.
    WHEN   You know which part is stable and want control over it.
    EXPECT call 1 = WRITE, call 2 = READ.
    """
    doc = build_handbook("Handbook (manual)")
    system = [{"type": "text", "text": doc, "cache_control": EPHEMERAL}]
    for i, q in enumerate(QUESTIONS[:2]):
        send(client, f"call {i + 1}", q, system=system, messages=user(q))


def ttl(client):
    """TTL: keep the entry alive for 1 hour instead of 5 minutes.

    WHAT   cache_control gets "ttl": "1h". The write costs 2x instead of 1.25x.
    WHEN   Requests with the same prefix arrive more than 5 minutes apart.
           If they arrive less than 5 minutes apart, the default is cheaper.
    EXPECT call 1 = WRITE, call 2 = READ.
    """
    doc = build_handbook("Handbook (ttl)")
    system = [{"type": "text", "text": doc,
               "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    for i, q in enumerate(QUESTIONS[:2]):
        send(client, f"call {i + 1}", q, system=system, messages=user(q))


def tools(client):
    """TOOLS: cache the tool definitions.

    WHAT   The marker goes on the LAST tool. Tools render first in the request
           (tools -> system -> messages), so this caches all of them.
    WHEN   You have many tools with long descriptions, for example MCP servers.
    EXPECT call 1 = WRITE, call 2 = READ.
           Adding, removing or reordering a tool breaks this cache.
    """
    tool_list = build_tools("Tools")
    tool_list[-1]["cache_control"] = EPHEMERAL  # on the LAST tool: caches all tools
    for i, q in enumerate(QUESTIONS[:2]):
        send(client, f"call {i + 1}", q, tools=tool_list, messages=user(q))


def conversation(client):
    """CONVERSATION: the breakpoint moves forward every turn.

    WHAT   One marker on the last block of the newest user turn. Each request
           reuses the whole earlier conversation and writes only the new part.
    WHEN   Multi-turn chats where the history keeps growing.
    EXPECT turn 1 = big WRITE; turns 2-3 = big READ plus a small WRITE.
    """
    doc = build_handbook("Handbook (conversation)")
    history: list[dict] = []
    for i, q in enumerate(QUESTIONS):
        first = [{"type": "text", "text": doc}] if i == 0 else []
        history.append({"role": "user", "content": first + [{"type": "text", "text": q}]})
        # Keep exactly one marker, on the last block of the newest user turn.
        for message in history:
            if message["role"] == "user":
                for block in message["content"]:
                    block.pop("cache_control", None)
        history[-1]["content"][-1]["cache_control"] = EPHEMERAL
        response = send(client, f"turn {i + 1}", q, messages=history)
        answer = next((b.text for b in response.content if b.type == "text"), "")
        history.append({"role": "assistant", "content": answer or "(no text)"})


def shared_prefix(client):
    """SHARED PREFIX: same big document, a different question every time.

    WHAT   The marker goes at the end of the SHARED part, not at the end of the
           whole prompt. The question after it carries no marker.
    WHEN   Many questions about one document or one set of instructions.
    EXPECT call 1 = WRITE, call 2 = READ.
           A marker on the question itself would write a new entry every time.
    """
    doc = build_handbook("Handbook (shared prefix)")
    for i, q in enumerate(QUESTIONS[:2]):
        content = [
            {"type": "text", "text": doc, "cache_control": EPHEMERAL},  # shared part
            {"type": "text", "text": q},  # varies, so NO marker here
        ]
        send(client, f"call {i + 1}", q, messages=[{"role": "user", "content": content}])


def multi(client):
    """MULTI: several breakpoints at once (tools, system, document).

    WHAT   Up to 4 markers per request. The cache matches the longest identical
           prefix, so a change late in the request keeps the earlier parts.
    WHEN   Parts change at different speeds: tools rarely, system sometimes,
           the document often.
    EXPECT call 1 = WRITE all, call 2 = READ all,
           call 3 (new document) = READ tools + system, WRITE only the document.
    """
    tool_list = build_tools("Multi")
    tool_list[-1]["cache_control"] = EPHEMERAL  # breakpoint 1: tools
    system = [{"type": "text", "text": "You answer questions about company policy. Be brief.",
               "cache_control": EPHEMERAL}]  # breakpoint 2: tools + system

    def request(doc: str, q: str) -> dict:
        content = [{"type": "text", "text": doc, "cache_control": EPHEMERAL},  # breakpoint 3
                   {"type": "text", "text": q}]
        return dict(tools=tool_list, system=system,
                    messages=[{"role": "user", "content": content}])

    doc_a = build_handbook("Handbook A (multi)")
    send(client, "call 1: everything is new", QUESTIONS[0], **request(doc_a, QUESTIONS[0]))
    send(client, "call 2: same everything", QUESTIONS[1], **request(doc_a, QUESTIONS[1]))
    doc_b = build_handbook("Handbook B (multi)").replace(f"[run {RUN_ID}]", f"[run {RUN_ID}-b]")
    send(client, "call 3: new document, same tools + system", QUESTIONS[2],
         **request(doc_b, QUESTIONS[2]))


SCENARIOS = {
    "automatic": automatic,
    "manual": manual,
    "ttl": ttl,
    "tools": tools,
    "conversation": conversation,
    "shared_prefix": shared_prefix,
    "multi": multi,
}


def main() -> None:
    names = sys.argv[1:] or list(SCENARIOS)
    unknown = [n for n in names if n not in SCENARIOS]
    if unknown:
        sys.exit(f"Unknown scenario(s): {unknown}. Choose from: {list(SCENARIOS)}")

    client = anthropic.Anthropic()
    print(f"Model: {MODEL}   run id: {RUN_ID}\n")
    for name in names:
        print("=" * 72)
        print(textwrap.indent(inspect.cleandoc(SCENARIOS[name].__doc__ or name), ""))
        print("-" * 72)
        try:
            SCENARIOS[name](client)
        except anthropic.APIStatusError as e:
            print(f"  FAILED ({e.status_code}): {e.message[:200]}")
        print()


if __name__ == "__main__":
    main()
