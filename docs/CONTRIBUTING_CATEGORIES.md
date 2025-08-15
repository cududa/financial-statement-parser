# Contributing Transaction Categories

The PNC Statement Parser uses a configurable JSON file to categorize transactions automatically. This makes it easy for users to contribute new categories and patterns through pull requests.

## Category Configuration File

The categories are defined in [`src/categories.json`](../src/categories.json) with this structure:

```json
{
  "categories": {
    "CategoryName": {
      "patterns": [
        "Pattern1",
        "Pattern2",
        "Regex.*Pattern"
      ]
    }
  }
}
```

## How to Add New Categories

### 1. Fork and Clone the Repository

```bash
git clone https://github.com/your-username/pnc-statement-parser.git
cd pnc-statement-parser
```

### 2. Edit the Categories File

Open `src/categories.json` and add your new category or patterns:

```json
{
  "categories": {
    "Medical": {
      "patterns": [
        "Cleveland Clinic",
        "MetroHealth",
        "Kaiser Permanente",
        "CVS Pharmacy"
      ]
    },
    "YourNewCategory": {
      "patterns": [
        "Merchant Name",
        "Another\\s+Merchant",
        "Regex.*Pattern"
      ]
    }
  }
}
```

### 3. Pattern Types

You can use two types of patterns:

#### Simple String Matching
```json
"Netflix"          // Matches any description containing "Netflix"
"Starbucks"        // Matches any description containing "Starbucks"
```

#### Regex Patterns
```json
"Nytimes\\*Nytimes"     // Matches "Nytimes*Nytimes" (escaping the *)
"Bp#\\d+"               // Matches "Bp#1234567" (BP gas stations)
"Apple\\.Com/Bill"      // Matches "Apple.Com/Bill" (escaping the .)
```

### 4. Category Examples

#### Medical
```json
"Medical": {
  "patterns": [
    "Cleveland Clinic",
    "MetroHealth",
    "Mhs\\*Metrohealth",
    "Kaiser Permanente",
    "CVS Pharmacy",
    "Walgreens",
    "Urgent Care",
    "Medical Center"
  ]
}
```

#### Transportation
```json
"Transportation": {
  "patterns": [
    "Uber",
    "Lyft", 
    "Shell",
    "Bp#\\d+",
    "Metro",
    "Transit"
  ]
}
```

#### Utilities
```json
"Utilities": {
  "patterns": [
    "Electric",
    "Gas Company",
    "Water Department",
    "Verizon",
    "Comcast"
  ]
}
```

### 5. Testing Your Changes

After making changes, test with a sample PDF:

```bash
python parse_statements_enhanced.py --file your_statement.pdf --output test.csv --verbose
```

Check that your new categories are being applied correctly.

### 6. Submit a Pull Request

1. Commit your changes:
   ```bash
   git add src/categories.json
   git commit -m "Add Medical category with Cleveland Clinic and MetroHealth patterns"
   ```

2. Push to your fork:
   ```bash
   git push origin main
   ```

3. Create a pull request on GitHub

## Guidelines for Contributions

### Category Naming
- Use clear, descriptive names: `"Medical"`, `"Transportation"`, `"Utilities"`
- Use singular form: `"Subscription"` not `"Subscriptions"`
- Capitalize properly: `"Food"` not `"food"`

### Pattern Guidelines
- **Be specific**: `"Cleveland Clinic"` is better than just `"Clinic"`
- **Use escaping**: Escape special regex characters like `\.`, `\*`, `\+`
- **Test thoroughly**: Make sure patterns don't accidentally match unrelated merchants
- **Regional awareness**: Consider regional variations (e.g., different pharmacy chains)

### Common Merchants to Consider

**Medical:**
- Hospital systems (Cleveland Clinic, Kaiser Permanente, Mayo Clinic)
- Pharmacies (CVS, Walgreens, Rite Aid)
- Dental offices, urgent care centers

**Transportation:**
- Ride sharing (Uber, Lyft)
- Gas stations (Shell, BP, Exxon, Marathon)
- Public transit systems

**Utilities:**
- Internet/Cable (Comcast, Spectrum, Verizon)
- Electric companies (varies by region)
- Phone services

## Review Process

Pull requests will be reviewed for:
1. **Accuracy**: Do the patterns correctly identify the intended merchants?
2. **Specificity**: Are patterns specific enough to avoid false matches?
3. **Completeness**: Are major merchants in the category included?
4. **Format**: Is the JSON properly formatted?

## Questions?

If you have questions about contributing categories:
1. Check existing categories for examples
2. Open an issue to discuss new category ideas
3. Test your patterns with sample data before submitting

Thank you for helping improve the PNC Statement Parser! 🎉