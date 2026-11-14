# Retail Profitability Intelligence Engine

**AI-Driven Retail Margin Optimization & Diagnostic Reporting System**\
Author: Arianne Rull\
Version: 1.0

------------------------------------------------------------------------

## 📌 Overview

The **Retail Profitability Intelligence Engine** is a modular
Python-based analytics system that transforms retail transaction data
into executive-ready insights.

It automates:

-   KPI calculation (Sales, COGS, Margin, Margin Rate)
-   Margin diagnostics across product and store dimensions
-   Anomaly detection using Isolation Forest
-   Margin driver modeling using XGBoost
-   Professional branded PDF report generation
-   Exportable analytics artifacts

------------------------------------------------------------------------

## 🎯 Business Objectives

This application enables stakeholders to:

-   Monitor revenue and profitability performance
-   Identify high-sales but low-margin segments
-   Detect abnormal pricing or cost patterns
-   Understand key drivers of margin performance
-   Generate an executive-ready performance report

------------------------------------------------------------------------

## 🏗 System Architecture

    retail_ai_case/
    │
    ├── main.py              # Orchestrates full pipeline
    ├── config.py            # Configuration settings
    ├── io_utils.py          # Excel ingestion
    ├── mapping.py           # Column auto-detection
    ├── kpi.py               # KPI calculations
    ├── analysis.py          # ML + diagnostics
    ├── viz.py               # Visualization engine
    ├── report.py            # Branded PDF generator
    ├── exporter.py          # CSV + ZIP exports
    ├── theme.py             # Visual branding styles
    └── CaseStudy_DataExtractFromPowerBIFile.xlsx

------------------------------------------------------------------------

## 💻 System Requirements

-   Python 3.10+
-   macOS / Windows / Linux

------------------------------------------------------------------------

## 📦 Installation

### Navigate to project folder

``` bash
cd /path/to/retail_ai_case
```

### Create virtual environment (recommended)

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

``` bash
python3 -m pip install -U pip
python3 -m pip install pandas numpy openpyxl scikit-learn matplotlib reportlab pillow xgboost
```

### macOS Users (XGBoost requirement)

``` bash
brew install libomp
```

------------------------------------------------------------------------

## ▶️ Running the Application

``` bash
python3 main.py --excel "CaseStudy_DataExtractFromPowerBIFile.xlsx" --pdf "Retail_Case_Report.pdf"
```

------------------------------------------------------------------------

## 📊 Output Files

Primary Output:

-   Retail_Case_Report.pdf

Supporting Artifacts:

-   case_outputs/
-   report_assets/

------------------------------------------------------------------------

## 🤖 Machine Learning Components

### Anomaly Detection

Model: Isolation Forest

### Margin Driver Model

Model: XGBoost Regressor

Target: `margin_rate`

------------------------------------------------------------------------

## 📌 What This Project Demonstrates

-   Modular production-style Python architecture\
-   Financial KPI automation\
-   Applied machine learning for business diagnostics\
-   Executive-ready reporting design\
-   End-to-end analytics engineering

------------------------------------------------------------------------

This project is intended for case study demonstration purposes.
