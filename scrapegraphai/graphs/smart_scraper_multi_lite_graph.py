"""
SmartScraperMultiGraph Module
"""

from copy import deepcopy
from typing import List, Optional, Type

from pydantic import BaseModel

from ..nodes import GraphIteratorNode, MergeAnswersNode
from ..utils.copy import safe_deepcopy
from .abstract_graph import AbstractGraph
from .base_graph import BaseGraph
from .smart_scraper_lite_graph import SmartScraperLiteGraph


class SmartScraperMultiLiteGraph(AbstractGraph):
    """
    SmartScraperMultiLiteGraph is a scraping pipeline that scrapes a
    list of URLs and merge the content first and finally generates answers to a given prompt.
    It only requires a user prompt and a list of URLs.
    The difference with the SmartScraperMultiGraph is that in this case the content is merged
    before to be passed to the llm.

    Attributes:
        prompt (str): The user prompt to search the internet.
        llm_model (dict): The configuration for the language model.
        embedder_model (dict): The configuration for the embedder model.
        headless (bool): A flag to run the browser in headless mode.
        verbose (bool): A flag to display the execution information.
        model_token (int): The token limit for the language model.

    Args:
        prompt (str): The user prompt to search the internet.
        source (List[str]): The source of the graph.
        config (dict): Configuration parameters for the graph.
        schema (Optional[BaseModel]): The schema for the graph output.

    Example:
        >>> smart_scraper_multi_lite_graph = SmartScraperMultiLiteGraph(
        ...     prompt="Who is ?",
        ...     source= [
        ...         "https://perinim.github.io/",
        ...         "https://perinim.github.io/cv/"
        ...     ],
        ...     config={"llm": {"model": "openai/gpt-3.5-turbo"}}
        ... )
        >>> result = smart_scraper_multi_lite_graph.run()
    """

    def __init__(
        self,
        prompt: str,
        source: List[str],
        config: dict,
        schema: Optional[Type[BaseModel]] = None,
    ):
        self.copy_config = safe_deepcopy(config)
        self.copy_schema = deepcopy(schema)
        super().__init__(prompt, config, source, schema)

    def _create_graph(self) -> BaseGraph:
        """
        Creates the graph of nodes representing the workflow for web scraping
        and parsing and then merge the content and generates answers to a given prompt.
        """
        graph_iterator_node = GraphIteratorNode(
            input="user_prompt & urls",
            output=["parsed_doc"],
            node_config={
                "graph_instance": SmartScraperLiteGraph,
                "scraper_config": self.copy_config,
            },
            schema=self.copy_schema,
        )

        merge_answers_node = MergeAnswersNode(
            input="user_prompt & parsed_doc",
            output=["answer"],
            node_config={"llm_model": self.llm_model, "schema": self.copy_schema},
        )

        return BaseGraph(
            nodes=[
                graph_iterator_node,
                merge_answers_node,
            ],
            edges=[
                (graph_iterator_node, merge_answers_node),
            ],
            entry_point=graph_iterator_node,
            graph_name=self.__class__.__name__,
        )

    def run(self) -> str:
        """
        Executes the web scraping and parsing process first and
        then concatenate the content and generates answers to a given prompt.

        Returns:
            str: The answer to the prompt.
        """
        inputs = {"user_prompt": self.prompt, "urls": self.source}
        self.final_state, self.execution_info = self.graph.execute(inputs)
        return self.final_state.get("answer", "No answer found.")
