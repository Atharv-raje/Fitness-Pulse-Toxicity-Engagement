# Data-Driven Fitness: Toxicity and Engagement Analysis

This project is a Flask-based web application that provides an interactive dashboard for analyzing fitness-related data from Reddit and 4chan. Users can select categories, date ranges, and analysis types (Toxicity or Engagement) to visualize trends and metrics over time.

## Features

- **Homepage**:  
  Presents two platform options: **Reddit Analysis** and **4chan Analysis**.

- **Platform Pages** (`/reddit` or `/4chan`):  
  Allows users to:
  - Choose between **Toxicity Analysis** or **Engagement Metrics**.
  - Select category filters (All, Fitness, Nutrition, Mental Health for Reddit; All, Fitness, Politics for 4chan).
  - Pick a start date and end date to define the analysis period.
  
  The application then queries a PostgreSQL database, fetches the data matching these criteria, and displays the results in line charts.

- **Dynamic Plots**:  
  Plots are generated server-side with Matplotlib, returned as PNGs, and displayed in the dashboard without page reloads (via updating the `src` of an `img` element).

- **Background and Theming**:  
  A custom background image , CSS to make the dashboard visually appealing.

## Project Structure

**app.py**:  
  Main Flask application. Contains routes for:
  - `/` (homepage)
  - `/<platform>` (platform analysis page)
  - `/api/plot/<platform>/<analysis_type>` (endpoint returning dynamically generated plots)

- **templates/index.html**:  
  The homepage, providing platform choices (Reddit, 4chan).

- **templates/platform.html**:  
  The page to select category, date range, and analysis type for a given platform, and display the resulting plots.

- **static/css/custom.css**:  
  Contains custom styling, background image references, and theme colors.

- **static/images/background.jpg**:  
  Background image for the dashboard

## Setup

**Create Virtual Environment**:
python -m venv venv

**Activate Virtual Environment**:
source venv/bin/activate

**Install Dependencies**:
pip insatll Flask psycopg2-binary pandas matplotlib

## RUN

With your virtual environment activated and dependencies installed, run:
python app.py


## NOTE
Once you run the code and view the Flask app, if you notice any irregularities in the graphs or plots, it might be a minor mistake that occurred while updating the database for Implementation otherwise everything works perfect
