# PNC Statement Parser - Technical Implementation Details

## Document Purpose
This document provides a comprehensive technical analysis of the **modular PNC statement parsing implementation** for independent review and validation. It details the new architecture, parsing methodology, data extraction strategies, filtering logic, and key design decisions.

## 🏗️ Architecture Overview (Updated August 2025)

### Modular Design Philosophy
The parser has been refactored into a **modular, extensible architecture** that separates concerns and enables future bank support:

```
src/parsers/
├── base_parser.py           # Abstract interface for all banks
├── pnc_statement_parser.py  # PNC-specific implementation
├── pnc_patterns.py          # All PNC regex patterns
├── section_extractor.py     # Section boundary handling
├── transaction_parser.py    # Core transaction parsing logic
├── categorization.py        # JSON-based auto-categorization
└── text_utils.py           # Text cleaning and utilities
```

### Component Interactions
```
PDFIngester → PNCStatementParser → SectionExtractor → TransactionParser
                     ↓                    ↓                ↓
              PNCPatterns         TextCleaner       TransactionCategorizer
```

---

## 1. PDF Structure Analysis Foundation

### Statement Format: PNC Virtual Wallet Spend Statement
**Sample Period Analyzed**: December 2022 to January 2023 (6-page statement)

### Key Document Patterns Identified

#### Header Structure
```
Virtual Wallet Spend Statement
PNC Bank
Primary account number: 31-6483-2157
Page 1 of 6
For the period 12/02/2022 to 01/03/2023 Number of enclosures: 0
```

#### Transaction Sections (in order)
1. **Deposits and Other Additions**
2. **Banking/Debit Card Withdrawals and Purchases** 
3. **Online and Electronic Banking Deductions**
4. **Daily Balance Detail** (NOT transaction data - balances only)

---

## 2. Critical Text Extraction Challenges

### Challenge 1: Extraneous Summary Text
**Problem**: Summary lines appear in the same columns as transaction data
**Examples Found**:
```
"There were 2 Deposits and Other Additions totaling $6,288.87."
"There was 1 Banking Machine Withdrawal totaling $100.99."
"There were 8 Debit Card/Bank card PIN POS purchases totaling $210.49."
"There were 122 other Banking Machine/Debit Card deductions totaling $3,603.67."
"There were 5 Online or Electronic Banking Deductions totaling $1,279.36."
```

**Solution**: Comprehensive regex-based filtering system with 16+ ignore patterns

### Challenge 2: Multi-Line Transaction Descriptions
**Problem**: Transaction descriptions span multiple lines
**Example**:
```
12/16    26.65    3767 Debit Card Purchase Uptown Mart
                  Lakewood
```

**Solution**: Intelligent continuation line detection that:
- Combines non-date lines with previous transaction
- Filters out extraneous continuation lines
- Preserves location and merchant details

### Challenge 3: Mixed Content in Transaction Areas
**Problem**: Headers, summaries, and actual transactions intermixed
**Solution**: Multi-layer filtering approach

---

## 3. Text Extraction Methodology

### Primary Tool: pdfplumber
- **Reason**: Superior text extraction for structured documents
- **Fallback**: PyPDF2 for compatibility
- **Page Handling**: Concatenates all pages with page markers

### Text Processing Pipeline
```
PDF → Raw Text Extraction → Page Combination → Section Identification → 
Line-by-Line Filtering → Transaction Parsing → Data Validation
```

---

## 4. Section Identification Strategy

### Section Boundary Detection
Uses regex patterns to identify major sections:

```python
DEPOSITS_START = r'Deposits and Other Additions'
WITHDRAWALS_START = r'Banking/Debit Card Withdrawals and Purchases'  
ONLINE_BANKING_START = r'Online and Electronic Banking Deductions'
DAILY_BALANCE_START = r'Daily Balance Detail'  # End marker
```

### Section Extraction Logic (SectionExtractor class)
1. **Find section start** using regex patterns from PNCPatterns
2. **Determine section end** by finding next section or end of document
3. **Extract section text** between boundaries
4. **Delegate to TransactionParser** for individual transaction parsing
5. **Return typed Transaction objects** with proper categorization

---

## 5. Transaction Line Identification

### Date Pattern Recognition
**Primary Pattern**: `^(\d{1,2}/\d{1,2})\s+`
- Matches: "12/08", "1/3", etc.
- **Critical**: Lines MUST start with this pattern to be considered transactions

### Amount Extraction
**Pattern**: `(\d{1,3}(?:,\d{3})*\.\d{2})`
- Handles: "38.87", "6,250.00", "1,103.00"
- **Critical**: Must find amount on same line as date

### Transaction Type Classification
Based on section location:
- **Deposits section** → CREDIT transactions
- **Withdrawals section** → DEBIT transactions  
- **Online Banking section** → DEBIT transactions

---

## 6. Extraneous Content Filtering System (TextCleaner class)

### Modular Filtering Architecture
The `TextCleaner` class in `text_utils.py` provides centralized text processing:
- Accepts `PNCPatterns` instance for pattern access
- Provides `is_extraneous_line()` method for filtering
- Includes `clean_description()` for contamination removal
- Supports `is_valid_merchant_continuation()` for multi-line handling

### Regex-Based Ignore Patterns (35+ patterns)

#### Summary Line Patterns
```python
r'^\s*There were?\s+\d+.*totaling.*\$.*$'        # "There were 2 Deposits..."
r'^\s*There was\s+\d+.*totaling.*\$.*$'          # "There was 1 Banking..."
r'^\s*There were?\s+\d+.*deductions.*totaling.*\$.*$'  # Deduction summaries
r'^\s*There were?\s+\d+.*purchases.*totaling.*\$.*$'   # Purchase summaries
r'^\s*There were?\s+\d+.*Banking Deductions.*totaling.*\$.*$'  # Banking summaries
```

#### Header/Footer Patterns
```python
r'^\s*Date\s+Amount\s+Description\s*$'           # Column headers
r'^\s*Virtual Wallet.*Statement\s*$'            # Document headers
r'^\s*PNC Bank\s*$'                              # Bank name
r'^\s*Primary account number:.*$'                # Account info
r'^\s*Page\s+\d+\s+of\s+\d+\s*$'               # Page numbers
r'^\s*continued on next page\s*$'                # Continuations
```

#### Section Header Patterns
```python
r'^\s*Activity Detail\s*$'                       # Section headers
r'^\s*Deposits and Other Additions\s*$'
r'^\s*Banking/Debit Card Withdrawals and Purchases\s*$'
r'^\s*Online and Electronic Banking Deductions\s*$'
r'^\s*Daily Balance Detail\s*$'
```

#### Standalone Data Patterns
```python
r'^\s*\$\d+\.\d{2}\s*$'                         # Standalone amounts
r'^\s*\d+\s*$'                                  # Standalone numbers
r'^\s*-+\s*$'                                   # Separator lines
```

### Heuristic Filtering
Additional logic for edge cases:
- **Short location suffixes**: Lines ≤3 characters that are alphabetic only
- **State abbreviations**: 2-character uppercase alphabetic lines
- **Account summary keywords**: Lines containing balance/summary terms

---

## 7. Transaction Parsing Algorithm (TransactionParser class)

### Modular Transaction Processing
The `TransactionParser` class orchestrates transaction extraction:
- Accepts `PNCPatterns` and `TransactionCategorizer` instances
- Uses `TextCleaner` for line filtering
- Uses `MerchantExtractor` for merchant information
- Returns fully-formed `Transaction` objects

### Single Transaction Extraction Process

1. **Identify transaction start**: Line matching date pattern from PNCPatterns
2. **Extract core data**: Date and amount from first line
3. **Parse description**: Text after amount on first line
4. **Collect continuation lines**: 
   - Include non-date lines that follow
   - **CRITICAL**: Filter using TextCleaner.is_extraneous_line()
   - Validate using TextCleaner.is_valid_merchant_continuation()
   - Stop at next date line or section boundary
5. **Combine description**: Join all valid continuation lines
6. **Clean description**: Apply TextCleaner.clean_description()
7. **Extract metadata**: Use MerchantExtractor for merchant/card info
8. **Auto-categorize**: Apply TransactionCategorizer patterns

### Multi-Line Description Handling
```python
# Example processing:
Line 1: "12/16    26.65    3767 Debit Card Purchase Uptown Mart"
Line 2: "                  Lakewood"
Line 3: "There were 8 Debit Card/Bank card PIN POS purchases..."  # FILTERED OUT

Result: "3767 Debit Card Purchase Uptown Mart Lakewood"
```

### Year Resolution Logic
**Challenge**: Dates in MM/DD format without year
**Solution**: 
- Extract statement period from header
- Handle year boundaries (Dec transactions in Jan statement)
- Assign appropriate year based on statement period context

---

## 8. Data Validation Strategy

### Three-Tier Validation

#### 1. Structural Validation
- Date format validation (MM/DD within statement period)
- Amount reasonableness (positive, < $50,000 threshold)
- Required field completeness

#### 2. Business Logic Validation  
- Transaction dates within statement period
- Amount signs match transaction types
- Balance calculation consistency

#### 3. Data Quality Checks
- Duplicate transaction detection
- Suspicious pattern identification
- Summary total reconciliation

---

## 9. Key Design Decisions & Rationale

### Decision 1: Section-Based Parsing
**Rationale**: PNC statements have clear section boundaries
**Implementation**: Parse each section independently to avoid cross-contamination
**Benefit**: Robust against formatting variations between sections

### Decision 2: Aggressive Extraneous Text Filtering
**Rationale**: Summary lines can easily be mistaken for transaction data
**Implementation**: Multi-layer filtering with both regex and heuristics
**Risk Mitigation**: Preserve raw lines for debugging, extensive testing

### Decision 3: Multi-Line Description Assembly
**Rationale**: Transaction descriptions frequently span multiple lines
**Implementation**: Continuation line detection with extraneous text filtering
**Challenge**: Balance completeness with accuracy

### Decision 4: Transaction Type by Section
**Rationale**: Section determines transaction nature more reliably than description parsing
**Implementation**: CREDIT for deposits, DEBIT for withdrawals/online banking
**Benefit**: Simplified logic, reduced error potential

### Decision 5: Year Inference from Statement Period
**Rationale**: Individual transactions lack year information
**Implementation**: Extract from statement header, handle year boundaries
**Edge Case**: December transactions in January statements

---

## 10. Critical Areas for Review

### High-Risk Parsing Areas

1. **Summary Line Contamination**
   - Lines like "There were 2 Deposits..." must be filtered
   - Risk: False positive transactions with incorrect amounts

2. **Multi-Line Description Boundaries**
   - Must correctly identify where transaction description ends
   - Risk: Including extraneous text or missing continuation lines

3. **Section Boundary Detection**
   - Must accurately identify where one section ends and another begins
   - Risk: Cross-section transaction contamination

4. **Year Assignment Logic**
   - Critical for transactions near year boundaries
   - Risk: Transactions assigned to wrong year

### Validation Checkpoints

1. **Transaction Count Validation**: Compare parsed count vs. statement summaries
2. **Amount Total Validation**: Verify section totals match statement summaries  
3. **Date Range Validation**: Ensure all transactions within statement period
4. **Duplicate Detection**: Flag potential parsing errors creating duplicates

---

## 11. Testing and Quality Assurance

### Test Coverage Areas

1. **Basic Functionality Tests** (`test_basic.py`)
   - Transaction model functionality
   - Regex pattern matching
   - Data processing pipeline
   - CSV export formatting

2. **Extraneous Text Filtering Tests** (`test_extraneous_filtering.py`)
   - All 16+ ignore patterns
   - Real summary line examples
   - Mixed content scenarios

3. **Integration Tests** (Manual with real PDFs)
   - End-to-end processing
   - Validation report accuracy
   - Output format verification

### Quality Metrics
- **Parsing Accuracy**: Target 95%+ transaction identification
- **False Positive Rate**: < 1% (extraneous lines parsed as transactions)
- **Data Integrity**: All amounts balance to statement totals

---

## 12. Potential Risks and Mitigations

### Risk 1: Unidentified Extraneous Text Patterns
**Mitigation**: 
- Comprehensive ignore pattern library
- Validation reports flag anomalies
- Manual review checkpoints

### Risk 2: Statement Format Changes
**Mitigation**:
- Modular parser design for easy updates
- Version detection for format variations
- Graceful degradation with error reporting

### Risk 3: OCR/Scanned PDFs
**Limitation**: Parser requires text-based PDFs
**Mitigation**: Clear error messages, OCR preprocessing recommendations

### Risk 4: Edge Case Transactions
**Examples**: Unusual amount formats, special characters in descriptions
**Mitigation**: Extensive validation, raw line preservation for debugging

---

## 13. Output Data Integrity

### CSV Export Validation
- **Amount Signing**: Credits positive, debits negative for spreadsheet compatibility
- **Date Formatting**: Standardized YYYY-MM-DD format
- **Data Types**: Proper numeric formatting for calculations
- **Character Encoding**: UTF-8 for special characters in merchant names

### Google Sheets Compatibility
- Optimized column order and data types
- Proper decimal formatting
- Category standardization for pivot tables
- Month/year columns for filtering

---

## 14. Modular Architecture Benefits

### Extensibility for Multi-Bank Support
The new modular design enables easy addition of other bank parsers:

```python
# Example: Bank of America parser
class BOAStatementParser(BaseStatementParser):
    def __init__(self):
        self.patterns = BOAPatterns()              # Bank-specific patterns
        self.categorizer = TransactionCategorizer() # Reuse categorization
        self.transaction_parser = TransactionParser(self.patterns, self.categorizer)
        self.section_extractor = SectionExtractor(self.patterns, self.transaction_parser)
```

### Reusable Components
- **BaseStatementParser**: Abstract interface with validation framework
- **TransactionCategorizer**: JSON-based categorization works for any bank
- **TextCleaner**: Contamination patterns can be shared/extended
- **Transaction Models**: Universal data structures

### General Purpose Patterns Ready for Reuse
- Date parsing (MM/DD format used by multiple banks)
- Amount extraction (comma/decimal handling)
- Section detection framework
- Multi-line description assembly
- Year boundary logic

### Testing Isolation
- Each component can be tested independently
- Pattern validation separate from parsing logic
- Categorization rules testable in isolation
- Text cleaning verifiable with unit tests

---

## 15. Recommended Review Process

### For Independent Review

1. **Verify Section Identification Logic**
   - Check regex patterns against sample PDF structure
   - Validate section boundary detection accuracy

2. **Test Extraneous Text Filtering**
   - Run filtering tests with known problematic lines
   - Verify all summary patterns are caught

3. **Validate Transaction Parsing Logic**
   - Review multi-line description assembly
   - Check year assignment algorithm
   - Verify amount extraction patterns

4. **Cross-Check Output Format**
   - Validate CSV structure matches requirements
   - Verify Google Sheets compatibility
   - Check data type conversions

5. **Review Error Handling**
   - Test with edge case inputs
   - Verify graceful failure modes
   - Check validation report completeness

---

## Conclusion

This implementation provides a robust, multi-layered approach to parsing PNC Virtual Wallet statements. The design prioritizes accuracy over completeness, with extensive filtering to prevent false positive transactions from extraneous text. The modular architecture supports future enhancements and format variations while maintaining data integrity through comprehensive validation.

**Key Strengths**:
- Comprehensive extraneous text filtering
- Robust multi-line description handling  
- Section-based parsing for accuracy
- Extensive validation and error reporting

**Areas for Continued Vigilance**:
- Statement format evolution
- New extraneous text patterns
- Edge case transaction formats
- Year boundary handling

This document should provide sufficient detail for independent technical review and validation of the parsing approach and implementation quality.

---

*Technical Implementation Document - August 2025*
*For independent review and validation of PNC statement parsing methodology*