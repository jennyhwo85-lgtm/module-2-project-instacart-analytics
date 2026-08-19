# Module 2 Assignment Project: Learner's Guide

> Source: [Module 2 Assignment Project V2 (Google Doc)](https://docs.google.com/document/u/0/d/1JgNqUk_hXLL2NdJv_UU2PLU-0cweaYemY_1HDvSA8Cg/mobilebasic)
> Saved into the repo on 2026-08-19 so the team can check progress against the original brief without needing Google Doc access.

## Overview

In this project, you will join a data engineering team to build a complete system for moving and analyzing data. You will start with raw data files, put them into a digital warehouse, clean them up, and then use Python to find helpful information.

At the end, you will present your work and what you discovered to both business leaders (like the CEO) and technical leaders (like the CTO). Your goal is to explain your technical steps in a way that everyone can understand and use to make better business decisions.

## Project Brief

### 1. Data Ingestion

- Pick one of these datasets to work with:
  - Brazilian E-Commerce Dataset by Olist
  - **Instacart Market Basket Analysis Dataset** (note: this dataset doesn't have a manual, but most labels are easy to figure out) ← *this is the dataset our team selected*
  - London Bicycles dataset (data is stored in the EU, so project settings must also use the EU location)
- You can use a different dataset if you prefer.
- Feel free to use any database tools you like, even if not covered in class.
- Load the data into your chosen database or data warehouse.
  - For example, write a Python script to upload CSV or Excel files into tables, or use any "ingestion" method.

### 2. Data Warehouse Design

- Plan a simple "star schema" structure for your e-commerce data.
- Organize data into "dimension" tables (like Customers and Products) and "fact" tables (like Sales).
- Implement the schema in your chosen database.

### 3. ELT Pipeline

- Use a tool like dbt (or any other method) to transform your raw data into your new organized tables.
- Implement data cleaning and validation steps.
- Create new columns for totals, such as total sale amount or how much a customer has spent over time.

### 4. Data Quality Testing

- Use tools like Great Expectations or write SQL queries to check that your data is correct.
- Check for missing info (nulls), duplicate entries, and mistakes in logic.

### 5. Data Analysis with Python

When building a data system, remember the goal: make it easy for analysts and business teams to use the data to find insights.

- Connect to the data warehouse using SQLAlchemy.
- Use the pandas library to explore the data and find patterns.
- Calculate key metrics like:
  - Monthly sales trends
  - Top-selling products
  - Customer segmentation by purchase behavior

### 6. Pipeline Orchestration (Optional)

Use an automation tool to manage the steps of your pipeline from start to finish. Set up a schedule so your data updates and quality checks run automatically. Options include (not limited to):

- Orchestration tools (Dagster, Airflow, etc.)
- Managed service (e.g., Google Cloud Composer)
- Cron jobs
- CI/CD via GitHub Actions

### 7. Documentation

- Create diagrams of your system using tools like DRAW.IO or EXCALIDRAW to show how data flows through your pipeline.
- Write a report that explains your technical choices and what you found in the data using charts and graphs.
  - Explain why certain tools were chosen over others, etc.
  - Explain why you decided to use your particular schema design and how it supports efficient querying (schema design justification).

### 8. Executive Stakeholder Presentation

Present your architecture and recommendations to executives using a slide deck. Focus on being clear and helpful.

**Recommended components:**

- Executive Summary: A quick 2–3 minute summary of the problem, your solution, and why it matters.
- Business Value: Explain how your work saves time, makes money, or helps the company reach its goals.
- Technical Overview: Explain how the system works at a high level without getting stuck in tiny details.
- Risks: Talk about what might go wrong and how you plan to fix or avoid those problems.
- Q&A: Be ready to answer questions simply and confidently to show you know your stuff.

**Presentation guidelines:**

- Duration: 10 minutes presentation + 5 minutes Q&A
- Audience: Assume a mixed audience of technical executives (CTOs, Engineering Directors) and business executives (CFOs, COOs, Business Leaders)
- Delivery: All team members should present and be prepared to answer questions
- Visuals: Use executive-friendly visuals (clear charts, architecture diagrams, ROI/KPI metrics), avoiding overly technical details
- Language: Balance technical credibility with business accessibility — avoid excessive jargon but demonstrate technical competence

## Deliverables

1. GitHub repository in a single main branch with all code and documentation
2. Jupyter notebooks with basic analysis
3. Slide deck to present the executive summary and key findings

## Evaluation Criteria

**Focus:**

- Accuracy and integrity of the data pipeline
- Quality of code and adherence to best practices
- Overall architecture and scalability of the solution
- Good documentation of the overall system — why certain designs and tools were chosen

**Good to have:**

- Depth of data analysis and insights generated
