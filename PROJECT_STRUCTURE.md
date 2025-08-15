# Project Structure Overview

## 🎯 Clean Organization

The PNC Statement Parser project is now organized with a clean, professional structure:

### Root Directory (Minimal & Clean)
```
/
├── parse_statements.py           # Main entry point (recommended)
├── README.md                     # Primary documentation
├── requirements.txt              # Dependencies
├── .gitignore                    # Git exclusions
└── PROJECT_STRUCTURE.md         # This file
```

### Core Code (`src/`)
All application logic is contained in the `src/` directory:

#### Modular Parser System (`src/parsers/`)
- **Base Framework**: `base_parser.py` - Abstract interface for all bank parsers
- **PNC Implementation**: `pnc_statement_parser.py` - Main PNC parser class
- **Pattern Definitions**: `pnc_patterns.py` - All PNC-specific regex patterns
- **Section Handling**: `section_extractor.py` - Deposits, withdrawals, online banking
- **Transaction Logic**: `transaction_parser.py` - Core parsing with multi-line support
- **Categorization**: `categorization.py` - JSON-based auto-categorization
- **Text Utilities**: `text_utils.py` - Cleaning and merchant extraction

#### Supporting Components
- **Data models**: Transaction and summary data structures in `models.py`
- **Processing**: Validation, cleaning, and export functionality
- **🆕 Year Processing**: `year_processor.py` - Multi-directory year processing and cross-year boundary handling
- **Categories**: `categories.json` for configurable transaction categorization
- **CLI interface**: `main.py` command-line entry point

### Documentation (`docs/`)
All planning and technical documentation:
- `PNC_Statement_Parser_Plan.md` - Original project plan
- `PNC_Statement_Structure_Analysis.md` - PDF structure analysis
- `chatgptplan.md` - Alternative approach documentation

### Experiments (`experiments/`)
Deprecated features and experimental code:
- `enhanced_parser.py` - [DEPRECATED] Layout-aware parsing
- `layout_analyzer.py` - [DEPRECATED] Coordinate-based analysis
- `parse_statements_enhanced.py` - [DEPRECATED] Enhanced CLI
- `README.md` - Explanation of deprecated features

### Testing (`tests/`)
Test suite for reliable functionality:
- `test_basic.py` - Core functionality tests
- `test_extraneous_filtering.py` - Text filtering validation

### Examples (`examples/`)
- `example_usage.py` - Demonstrates basic parsing with JSON categorization

### Data Directories
- `data/` - Input directory for PDF files (gitignored)
- `output/` - Output directory for CSV files (gitignored)
- `PNC_Documents/` - Private statement storage (gitignored)

## 🔒 Security & Privacy

The `.gitignore` file ensures sensitive data is never committed:
- All PDF files (`*.pdf`)
- All CSV outputs (`*.csv`)
- Private document directories
- Virtual environment files

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests**:
   ```bash
   python tests/test_basic.py
   ```

3. **Process statements**:
   ```bash
   # Basic parsing with categorization (recommended)
   python parse_statements.py --file statement.pdf --output output.csv
   
   # Process directory with monthly files
   python parse_statements.py --directory statements/ --output all.csv --monthly
   
   # 🆕 Year processing mode (auto-discovers files)
   python parse_statements.py --year 2023 --output 2023_complete.csv
   
   # Year mode with cross-year boundary completion
   python parse_statements.py --year 2023 --include-next-month --output 2023.csv
   ```

## 📦 Package Installation

For development installation:
```bash
pip install -e .
```

This creates a command-line entry:
- `pnc-parse` - Basic parser with JSON categorization

## 🎯 Modular Architecture Benefits

### Extensibility for Multi-Bank Support
The new `src/parsers/` structure is designed for easy extension:

```python
# Adding new bank support
class ChaseStatementParser(BaseStatementParser):
    def __init__(self):
        self.patterns = ChasePatterns()
        self.categorizer = TransactionCategorizer()
        # Reuse existing components
```

### Category Contribution
The parser uses `src/categories.json` for transaction categorization:
```json
{
  "categories": {
    "Medical": {
      "patterns": ["Cleveland Clinic", "MetroHealth", "Mhs\\*Metrohealth"]
    }
  }
}
```
Users can submit PRs to expand categories for the community!

## 🧪 Development Workflow

1. **Make changes** in `src/`
2. **Test changes** with `tests/`
3. **Document** in `docs/`
4. **Example usage** in `examples/`

## 📋 File Organization Benefits

- **Clean root**: Only essential files at top level
- **Logical grouping**: Related files in appropriate directories
- **Easy navigation**: Clear purpose for each directory
- **Professional structure**: Standard Python project layout
- **Security focused**: Sensitive data properly excluded
- **Experimental isolation**: Deprecated features in experiments/ directory
- **Community contributions**: JSON-based categories for easy PR submissions

---

*Project structure organized for clarity, maintainability, and professional development.*