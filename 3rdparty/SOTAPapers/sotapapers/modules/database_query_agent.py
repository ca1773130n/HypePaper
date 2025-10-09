from sotapapers.core.agent import Agent
from sotapapers.core.settings import Settings
from sotapapers.core.database import DataBase
from sotapapers.modules.llm.llama_cpp_client import LlamaCppClient
import loguru
from sqlalchemy import text
import re

class DatabaseQueryAgent(Agent):
    def __init__(self, settings: Settings, logger: loguru.logger, db: DataBase):
        self.settings = settings
        self.log = logger
        self.db = db
        raw_system_prompt_content = self.settings.config.llm.prompts.sql_generation
        
        # Ensure system_prompt is a list of strings, then join it.
        if isinstance(raw_system_prompt_content, str):
            llm_system_prompt = raw_system_prompt_content
        elif hasattr(raw_system_prompt_content, '__iter__'):
            llm_system_prompt = "\n".join(list(raw_system_prompt_content))
        else:
            llm_system_prompt = str(raw_system_prompt_content)

        self.llm_client = LlamaCppClient(settings, logger, llm_system_prompt, temperature=0.5)

    def query_database_natural_language(self, natural_language_query: str):
        prompt = f"Convert the following natural language query into a SQL query for a SQLite database. The database has tables 'papers' and 'users'.\n\nNatural Language Query: {natural_language_query}\n\nSQL Query:"
        thoughts, sql_query = self.llm_client.run(prompt)
        
        # Strip whitespace from the raw LLM response before regex matching
        sql_query = sql_query.strip()

        # Clean up the SQL query
        # First, try to extract from ```sql block
        match = re.search(r'```sql\n(.*?)\n```', sql_query, re.DOTALL)
        if match:
            sql_query = match.group(1).strip()
        else:
            # Fallback: try to find the start of a SQL query (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP)
            # and assume the rest is the query.
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
            found_keyword_index = -1
            for keyword in sql_keywords:
                index = sql_query.upper().find(keyword)
                if index != -1 and (found_keyword_index == -1 or index < found_keyword_index):
                    found_keyword_index = index
            
            if found_keyword_index != -1:
                sql_query = sql_query[found_keyword_index:].strip()
            else:
                self.log.error(f"LLM response does not contain a recognizable SQL query: {sql_query}")
                return {"error": "LLM failed to produce a valid SQL query."}

        # Final check to remove conversational prefixes if any remain
        conversational_prefixes = ["Here is the SQL query:", "Here is the SQL query for your request:", "SQL Query:"]
        for prefix in conversational_prefixes:
            if sql_query.lower().startswith(prefix.lower()):
                sql_query = sql_query[len(prefix):].strip()
                break
        
        self.log.info(f"Generated SQL Query: {sql_query}")

        try:
            with self.db.Session() as session:
                result = session.execute(text(sql_query))
                
                # For SELECT statements, fetch results
                if sql_query.lower().startswith("select"):
                    columns = result.keys()
                    rows = result.fetchall()
                    return {"columns": list(columns), "rows": [list(row) for row in rows]}
                else:
                    session.commit()
                    return {"message": "Query executed successfully."}
        except Exception as e:
            self.log.error(f"Error executing SQL query: {e}")
            return {"error": str(e)} 