"""A tiny MCP server that shows the three things a server can expose.

- TOOL:     an action the model decides to call        (search_notes, add_note)
- RESOURCE: read-only data the client fetches by address (notes://list, notes://{note_id})
- PROMPT:   a ready-made instruction template            (summarize_note)
"""
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("notes")

# In-memory data. It resets every time the server starts.
NOTES: dict[str, str] = {
    "1": "MCP servers expose tools, resources and prompts.",
    "2": "Hooks are code that runs at lifecycle events, so they always fire.",
    "3": "Skills load only when the task matches their description.",
}


# --- TOOLS: the model chooses to call these ---------------------------------
@mcp.tool()
def search_notes(query: str) -> str:
    """Search the notes for a word and return the matching ones."""
    hits = [f"{i}: {t}" for i, t in NOTES.items() if query.lower() in t.lower()]
    return "\n".join(hits) or "No notes matched."


@mcp.tool()
def add_note(text: str) -> str:
    """Add a new note and return its id."""
    note_id = str(len(NOTES) + 1)
    NOTES[note_id] = text
    return f"Added note {note_id}."


# --- RESOURCES: read-only data, fetched by address --------------------------
@mcp.resource("notes://list")  # direct resource: fixed address, no parameters
def list_notes() -> str:
    """The ids and text of all notes."""
    return "\n".join(f"{i}: {t}" for i, t in NOTES.items())


@mcp.resource("notes://{note_id}")  # templated resource: the address has a parameter
def get_note(note_id: str) -> str:
    """One note, by id."""
    return NOTES.get(note_id, f"No note with id {note_id}.")


# --- PROMPTS: a vetted instruction the user invokes by name -----------------
@mcp.prompt()
def summarize_note(note_id: str) -> str:
    """Summarize one note in a single sentence."""
    return (
        f"Read the resource notes://{note_id} and summarize it in exactly one "
        "sentence. Start the answer with 'Summary (from notes server):'."
    )


if __name__ == "__main__":
    mcp.run()  # stdio transport: Claude Code starts this process and talks over stdin/stdout
