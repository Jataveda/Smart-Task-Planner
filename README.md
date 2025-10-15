# Smart-Task-Planner
The Smart Task Planner is an AI-assisted productivity application designed to transform high-level user goals into actionable task plans with logical timelines and dependencies. Its primary objective is to simplify project planning by leveraging natural-language reasoning to automatically structure objectives into sequential, time-bound steps
For example, when a user enters a goal such as “Launch a product in 2 weeks,” the system generates a complete plan including individual tasks like “Define scope,” “Design & plan,” “Implementation,” “Testing,” and “Launch,” each with appropriate start and end dates.

The system follows a full-stack architecture consisting of a FastAPI backend and a lightweight web frontend built with HTML, CSS, and JavaScript. The backend acts as an intelligent API layer that processes goal text, infers duration using heuristic or LLM-based reasoning, and distributes the total timeframe across interdependent tasks. A mock LLM engine is included to ensure the application runs without external dependencies, while optional integration with the OpenAI API enables richer reasoning when available. The backend also uses SQLite via SQLAlchemy ORM for persistent storage of plans and tasks.

The frontend provides an intuitive interface for goal input and visualizes the generated plan dynamically. Users can view all tasks, their dependencies, and estimated timelines in a clean, minimal layout.

Overall, the Smart Task Planner showcases an end-to-end AI-driven planning workflow combining natural-language understanding, timeline generation, and web-based visualization in a compact, deployable system.
