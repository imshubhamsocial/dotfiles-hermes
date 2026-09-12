class SymbolEntry:
    """Represents a single symbol found during index parsing."""
    def __init__(self, name, kind, signature):
        self.name = name
        self.kind = kind
        self.signature = signature
        self.docstring_token_length = 0

    def __repr__(self):
        return f"<SymbolEntry name={self.name} kind={self.kind}>"

class SymbolIndexer:
    """The core component responsible for traversing code and indexing symbols."""
    def __init__(self):
        self.index = {}

    def index_symbol(self, symbol_entry):
        """Records a symbol entry in the global index."""
        self.index[symbol_entry.name] = symbol_entry

    def parse_function(self, symbol_entry):
        """
        Parses a symbol and enriches it with metadata.
        NOTE: This method currently holds the logic for metadata extraction.
        """
        print(f"Processing function: {symbol_entry.name}")
        docstring = symbol_entry.docstring.strip() if symbol_entry.docstring else ""
        tokens = docstring.split()
        symbol_entry.docstring_token_length = len(tokens)
        pass
