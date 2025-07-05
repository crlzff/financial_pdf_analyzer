# Financial PDF Analyzer

An AI-powered web application that extracts and analyzes key financial metrics from PDF financial statements. Built with Streamlit and OpenRouter AI.

## Features

- **Multi-Company Analysis**: Automatically identifies and separates financial data by company
- **AI-Powered Extraction**: Uses advanced language models to find and calculate financial metrics
- **Smart Calculations**: Automatically calculates EBITDA, EBIT, and PFN when not explicitly stated
- **Multi-Year Tracking**: Organizes financial data by company and fiscal year
- **Interactive Visualizations**: Generates trend charts and comparative analysis
- **Data Export**: Download results as CSV for further analysis
- **Debug Mode**: Full transparency into AI processing and data extraction

## Supported Financial Metrics

- Revenue/Sales
- EBITDA (calculated if not present)
- EBIT (calculated if not present)
- Net Income
- Total Assets
- Total Liabilities
- Shareholders' Equity
- Operating Cash Flow
- Free Cash Flow
- Debt-to-Equity Ratio
- PFN (Net Financial Position - calculated automatically)

## Setup

### Prerequisites

- Python 3.8+
- OpenRouter API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```

### Configuration

1. Open the application in your browser
2. Enter your OpenRouter API key in the sidebar
3. Select your preferred AI model
4. Choose which financial metrics to extract

## Usage

1. **Upload Documents**: Upload one or more PDF financial statements
2. **Select Metrics**: Choose which financial data points to extract
3. **Analyze**: Click "Analyze Financial Documents" to process
4. **Review Results**: View extracted data organized by company and year
5. **Export**: Download results as CSV for further analysis

## Supported Document Types

- Annual reports
- Financial statements
- Balance sheets
- Income statements
- Italian and English financial documents

## AI Models

The application supports multiple AI models through OpenRouter:
- Anthropic Claude Sonnet 4
- Anthropic Claude Opus 4
- Google Gemini 2.5 Flash Preview
- Google Gemini 2.5 Pro Preview
- OpenAI GPT-4.1

## Key Capabilities

### Intelligent Company Identification
- Automatically extracts company names from documents
- Normalizes company names to prevent duplicates
- Handles document formatting artifacts (e.g., "Company 1 ABC SRL" becomes "ABC SRL")

### Smart Financial Calculations
- Calculates EBITDA from EBIT + Depreciation when not explicitly stated
- Determines PFN from bank debts minus cash positions
- Handles different accounting standards and formats

### Multi-Document Processing
- Processes multiple PDFs simultaneously
- Organizes results by company and fiscal year
- Generates comparative visualizations across time periods

## Security

- API keys are handled locally and never stored

## Requirements

```
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.1.0
plotly>=5.15.0
PyPDF2>=3.0.1
openpyxl>=3.1.2
```

## Limitations

- Requires OpenRouter API key (user-provided)
- PDF text extraction quality depends on document format
- Scanned documents may require OCR preprocessing
- Large documents (>50MB) may have slower processing times
