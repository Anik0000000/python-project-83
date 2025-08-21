# Page Analyzer
****

## Project Description

Page Analyzer is a website that analyzes specified pages for SEO readiness, similar to PageSpeed Insights.
****

### Hexlet tests and linter status:

[![Actions Status](https://github.com/Anik0000000/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/Anik0000000/python-project-83/actions)
[![PyCI](https://github.com/anik0000000/python-project-83/actions/workflows/pyci.yml/badge.svg)](https://github.com/anik0000000/python-project-83/actions/workflows/pyci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Anik0000000_python-project-83&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Anik0000000_python-project-83)

[//]: # ([Демонстрация проекта на render.com]&#40;https://python-project-83-g9q6.onrender.comm&#41;)

### Technologies Used:

| Инструмент                                                                       | Описание                                                                                                                                                                                                                                                                    |
|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [uv](https://docs.astral.sh/uv/)                                                 | "is an extremely fast Python package manager written in Rust. It is designed as a replacement for pip and pip-tools. It can also replace venv and pyenv."                                                                                                                   |            |
| [ruff](https://docs.astral.sh/ruff/)                                             | "Your Tool For Linter and Style Guide Enforcement"                                                                                                                                                                                                                          |
| [Flask](https://flask.palletsprojects.com/en/stable/)                            | "Flask is a lightweight WSGI web application framework. It is designed to make getting started quick and easy, with the ability to scale up to complex applications"                                                                                                        |
| [Gunicorn](https://docs.gunicorn.org/en/latest/index.html)                       | "Gunicorn ‘Green Unicorn’ is a Python WSGI HTTP Server for UNIX. It’s a pre-fork worker model ported from Ruby’s Unicorn project. The Gunicorn server is broadly compatible with various web frameworks, simply implemented, light on server resources, and fairly speedy." |
| [python-dotenv](https://pypi.org/project/python-dotenv/)                         | "Python-dotenv reads key-value pairs from a .env file and can set them as environment variables. It helps in the development of applications following the 12-factor principles."                                                                                           |
| [Bootstrap](https://getbootstrap.com/docs/5.3/getting-started/introduction/)     | "Bootstrap is a powerful, feature-packed frontend toolkit. Build anything—from prototype to production—in minutes."                                                                                                                                                         |
| [Psycopg](https://getbootstrap.com/docs/5.3/getting-started/introduction/)       | "Psycopg – PostgreSQL database adapter for Python"                                                                                                                                                                                                                          |
| [validators](https://validators.readthedocs.io/en/latest/#module-validators.url) | "Python Data Validation for Humans™."                                                                                                                                                                                                                                       |
| [Requests](https://requests.readthedocs.io/en/latest/)                           | "Requests is an elegant and simple HTTP library for Python, built for human beings."                                                                                                                                                                                        |
| [Beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)          | "Beautiful Soup is a Python library for pulling data out of HTML and XML files."                                                                                                                                                                                            |

---

## Installation

### Clone the repository:

```
git clone git@github.com:anik0000000/python-project-83
```

```
cd python-project-83
```

### To use this application, you need to configure the .env file.

After cloning the repository, rename the .env_example file to .env. Inside the file, you will find the SECRET_KEY and
DATABASE_URL variables. Replace their values with your own.
****

### Next, use the command below to install the required dependencies and generate the database tables.

```
make build
```

### Start the application with the following command:

```
make dev
```