from app.services.neo4j_real_service import Neo4jRealService
from app.services.bridge_entity_extractor import BridgeEntityExtractor
from app.services.word_parser_service import WordParserService
from app.services.word_content_analyzer import WordContentAnalyzer
from typing import Dict, List, Any
import logging
import uuid
import os

logger = logging.getLogger(__name__)

class KnowledgeGraphEngine:
    def __init__(self):
        try:
            self.neo4j_service = Neo4jRealService()
            self.word_parser_service = WordParserService()
            self.word_content_analyzer = WordContentAnalyzer() # Uses BridgeEntityExtractor internally
        except Exception as e:
            logger.error(f"Failed to initialize services in KnowledgeGraphEngine: {e}")
            raise
        # BridgeEntityExtractor is used by WordContentAnalyzer and build_graph_from_document
        # If build_graph_from_document is to be kept separate for non-Word docs, it needs its own instance or access.
        # For now, WordContentAnalyzer has its own. If build_graph_from_document is called by build_graph_from_word_document,
        # then self.entity_extractor might be redundant if all text processing goes through word_content_analyzer.
        # However, the original build_graph_from_document directly uses self.entity_extractor.
        # Let's keep it for now, assuming build_graph_from_document can be called directly for plain text.
        self.entity_extractor = BridgeEntityExtractor()


    def build_graph_from_word_document(self, file_path: str, document_name: str) -> Dict:
        """
        Builds a knowledge graph from a Word document.
        1. Parses Word document content using WordParserService.
        2. Analyzes professional content using WordContentAnalyzer (determines doc type, extracts params).
        3. Extracts entities and relationships from the text content by calling build_graph_from_document.
        4. Builds the knowledge graph and stores it in Neo4j (handled by build_graph_from_document).
        Returns a summary of the build process.
        """
        logger.info(f"Starting graph construction from Word document: {document_name} at {file_path}")
        try:
            # 1. Parse Word document
            parsed_content = self.word_parser_service.extract_text_content(file_path)
            tables = self.word_parser_service.extract_tables(file_path)

            text_for_extraction = parsed_content.get("text")
            if not text_for_extraction:
                logger.warning(f"No text content extracted from Word document: {document_name}")
                return {
                    "status": "Error: No text content from Word file", "document_name": document_name,
                    "nodes_created": 0, "rels_created": 0
                }

            # 2. Analyze professional content to guess document type and extract specific features
            # Extract headers and sections for context and potential use in analyzers
            sections_data = self.word_parser_service.extract_headers_and_sections(file_path)
            if sections_data.get("error"):
                logger.warning(f"Could not extract sections from {document_name}: {sections_data.get('error')}")
                sections_data = None # Proceed without section data if extraction fails

            # 2. Analyze professional content
            # Identify document type
            identified_doc_type = self.word_content_analyzer.identify_document_type(
                text_content_dict=parsed_content,
                tables=tables,
                sections=sections_data
            )
            logger.info(f"Identified document type for {document_name} as: {identified_doc_type}")

            # Perform analysis based on identified type
            specific_analysis_results = None
            if identified_doc_type == "Technical Standard":
                specific_analysis_results = self.word_content_analyzer.analyze_technical_standard(parsed_content, sections_data)
            elif identified_doc_type == "Design Specification":
                specific_analysis_results = self.word_content_analyzer.analyze_design_specification(parsed_content, sections_data)
            elif identified_doc_type == "Construction Manual":
                specific_analysis_results = self.word_content_analyzer.analyze_construction_manual(parsed_content, sections_data)
            else: # Default or Unknown
                logger.info(f"No specific analyzer for document type '{identified_doc_type}'. Performing generic entity extraction.")
                # Basic entity extraction if type is unknown or general
                specific_analysis_results = {"info": f"Generic analysis for document type: {identified_doc_type}",
                                             "extracted_entities": self.entity_extractor.extract_professional_entities(text_for_extraction),
                                             "extracted_relations": [] # Basic extract_professional_entities doesn't do relations.
                                             }


            # Extract technical parameters from tables
            table_parameters_extraction = self.word_content_analyzer.extract_technical_parameters(tables)

            # TODO: Integrate extracted table parameters and specific analysis results (clauses, formulas, etc.)
            # into the knowledge graph. This involves creating appropriate nodes and relationships.
            # For now, these results will be part of the summary.
            # Example: Create "Parameter" nodes, "Clause" nodes, etc.

            # For MVP, we primarily rely on build_graph_from_document for general entity/relation graph creation.
            # The specialized extractions (clauses, table params) are logged and returned in summary.
            # Future: These specialized items should become distinct graph elements.

            logger.info(f"Extracted parameters from tables in {document_name}: { {k: len(v) for k, v in table_parameters_extraction.items()} }")

            # 3. & 4. Build base graph using the main text content via existing method
            graph_build_summary = self.build_graph_from_document(
                text=text_for_extraction,
                document_name=document_name,
                document_type=identified_doc_type # Pass the identified type
            )

            # Enhance the summary with Word-specific processing information
            graph_build_summary["word_document_path"] = file_path
            graph_build_summary["word_metadata"] = parsed_content.get("metadata", {})
            graph_build_summary["identified_document_type"] = identified_doc_type
            graph_build_summary["specific_analysis_summary"] = specific_analysis_results # Includes entities/relations from analyzer
            graph_build_summary["tables_summary"] = {
                "table_count": len(tables) if isinstance(tables, list) and not (tables and tables[0].get("error")) else 0,
                "parameter_extraction_summary": {k: len(v) for k, v in table_parameters_extraction.items()}
                # "parameter_details": table_parameters_extraction # Can be very verbose
            }

            # Log the specialized info that's not yet fully in graph (MVP)
            if specific_analysis_results:
                if "clauses" in specific_analysis_results and specific_analysis_results["clauses"]:
                    logger.info(f"Found {len(specific_analysis_results['clauses'])} clauses/articles in {document_name}.")
                if "calculation_formulas" in specific_analysis_results and specific_analysis_results["calculation_formulas"]:
                    logger.info(f"Found {len(specific_analysis_results['calculation_formulas'])} potential formulas in {document_name}.")

            logger.info(f"Successfully processed Word document {document_name} for graph construction. Base graph built, specialized content analyzed.")
            return graph_build_summary

        except Exception as e:
            logger.exception(f"Error building graph from Word document {document_name} at {file_path}: {e}")
            return {
                "status": "Error during Word document graph construction",
                "document_name": document_name,
                "file_path": file_path,
                "error": str(e),
                "nodes_created": 0,
                "rels_created": 0
            }

    def build_graph_from_document(self, text: str, document_name: str, document_type: str = "unknown") -> Dict:
        """
        Builds a knowledge graph from a given document text.
        1. Extracts professional entities using self.entity_extractor.
        2. Identifies relationships between entities.
        3. Stores entities and relationships into Neo4j.
        4. Returns a summary of the build process.
        """
        logger.info(f"Starting graph construction for document: {document_name}")

        try:
            # 1. Extract professional entities
            # entities_by_category: Dict[str, List[Dict[str, str]]]
            # where each dict is {'term': <term>, 'sub_category': <sub_cat>, 'category': <cat>}
            entities_by_category = self.entity_extractor.extract_professional_entities(text)
            if not entities_by_category:
                logger.warning(f"No entities extracted from document: {document_name}")
                return {"status": "No entities found", "document_name": document_name, "nodes_created": 0, "rels_created": 0}

            processed_entities_count = 0
            created_nodes_ids = {} # Maps entity term+category to Neo4j node ID to avoid duplicates

            # 3. Store entities to Neo4j
            # We need to decide on node labels and properties.
            # Node label could be the main category (e.g., "结构类型", "材料类型")
            # Properties could include 'name' (the term), 'sub_category', and 'source_document'.

            for category, entity_list in entities_by_category.items():
                for entity_info in entity_list:
                    term = entity_info["term"]
                    sub_category = entity_info["sub_category"]

                    # Create a unique key for this entity to avoid creating duplicate nodes if the same term appears multiple times
                    # A more robust approach might involve more sophisticated entity resolution.
                    entity_key = (term, category) # Using term and main category as a composite key for uniqueness

                    if entity_key not in created_nodes_ids:
                        properties = {
                            "name": term, # 'name' is often a primary property for nodes
                            "sub_category": sub_category,
                            "source_document": document_name,
                            # Potentially add a unique ID if 'name' isn't guaranteed unique across all contexts
                            # "entity_uuid": str(uuid.uuid4())
                        }
                        # The Neo4j service's create_bridge_entity expects an entity_type (label)
                        # We'll use the 'category' as the primary label.
                        # We could also add sub_category as another label if desired.
                        node_id = self.neo4j_service.create_bridge_entity(entity_type=category, properties=properties)

                        if node_id:
                            created_nodes_ids[entity_key] = node_id
                            processed_entities_count += 1
                            logger.debug(f"Created node for entity: {term} ({category}) with ID: {node_id}")
                        else:
                            logger.error(f"Failed to create node for entity: {term} ({category})")

            logger.info(f"Processed {processed_entities_count} unique entities from document: {document_name}")

            # 2. Identify entity relationships (after entities are known and potentially have IDs)
            # extracted_relationships: List[Dict[str, Any]]
            # where each dict is {'subject': <term1>, 'object': <term2>, 'relation': <type>,
            # 'subject_details': entity1_info, 'object_details': entity2_info, 'context': <sentence>}
            extracted_relationships = self.entity_extractor.extract_relationships(text, entities_by_category)

            processed_relationships_count = 0
            if not extracted_relationships:
                logger.info(f"No relationships extracted or to be created for document: {document_name}")
            else:
                logger.info(f"Attempting to create {len(extracted_relationships)} relationships for document: {document_name}")
                for rel_info in extracted_relationships:
                    subject_term = rel_info["subject"]
                    object_term = rel_info["object"]
                    subject_category = rel_info["subject_details"]["category"]
                    object_category = rel_info["object_details"]["category"]
                    relation_type = rel_info["relation"]
                    rel_properties = {"source_document": document_name, "context": rel_info.get("context", "")[:250]} # Limit context length

                    # Get Neo4j IDs for subject and object nodes
                    subject_node_key = (subject_term, subject_category)
                    object_node_key = (object_term, object_category)

                    subject_node_id = created_nodes_ids.get(subject_node_key)
                    object_node_id = created_nodes_ids.get(object_node_key)

                    if subject_node_id and object_node_id:
                        # Use the new method that creates relationships using element IDs
                        success = self.neo4j_service.create_relationship_by_element_ids(
                            start_node_element_id=subject_node_id,
                            end_node_element_id=object_node_id,
                            rel_type=relation_type.upper().replace(" ", "_"), # Ensure valid Cypher relationship type
                            properties=rel_properties
                        )

                        if success:
                            processed_relationships_count += 1
                            logger.debug(f"Created relationship: ({subject_term})-[{relation_type}]->({object_term})")
                        else:
                            logger.error(f"Failed to create relationship: ({subject_term})-[{relation_type}]->({object_term})")
                    else:
                        logger.warning(f"Skipping relationship due to missing node ID(s): Subj ID: {subject_node_id}, Obj ID: {object_node_id} for rel: {subject_term} -> {object_term}")

            logger.info(f"Successfully created {processed_relationships_count} relationships for document: {document_name}")

            return {
                "status": "Graph construction complete",
                "document_name": document_name,
                "entities_found_by_category": {cat: len(ents) for cat, ents in entities_by_category.items()},
                "unique_entities_processed": processed_entities_count,
                "relationships_extracted": len(extracted_relationships),
                "relationships_created_in_db": processed_relationships_count,
                # "created_node_ids": created_nodes_ids # Might be too verbose for summary
            }

        except Exception as e:
            logger.exception(f"Error during graph construction for document {document_name}: {e}")
            return {
                "status": "Error during graph construction",
                "document_name": document_name,
                "error": str(e),
                "nodes_created": 0,
                "rels_created": 0
            }

    def query_graph_knowledge(self, query: str) -> List[Dict]:
        """
        Based on a natural language query, retrieves relevant knowledge from the graph.
        This is a placeholder and would require significant NLP and query mapping logic.
        For MVP, this might just pass keywords to neo4j_service.search_entities.
        """
        logger.info(f"Received graph query: {query}")

        # Basic MVP implementation:
        # 1. Try to extract keywords or potential entity names from the query.
        #    (This itself is an NLP task, for now, just use the whole query as keywords or split it)
        keywords = query.split() # Simplistic keyword extraction

        # 2. Search for entities related to these keywords.
        try:
            # No specific entity types provided, so search all.
            # Or, we could try to parse entity types from the query if it's structured.
            search_results = self.neo4j_service.search_entities(keywords=keywords, entity_types=None)

            if not search_results:
                return [{"message": "No direct entity matches found for your query."}]

            # 3. For each found entity, maybe get its neighbors to provide context.
            # This could result in a lot of data; needs careful handling.
            # For now, just return the direct search results.
            # A more advanced version would try to interpret the query to form specific Cypher queries.

            # Example: if query is "Tell me about Golden Gate Bridge"
            # search_entities might find "Golden Gate Bridge" node.
            # Then, get_entity_neighbors for that node.

            # Limit the number of results or depth of neighborhood for performance.
            # For now, returning the direct search results.
            formatted_results = []
            for entity_data in search_results[:10]: # Limit to 10 results for brevity
                # entity_data is like: {'id': 'xyz', 'types': ['TypeA'], 'name': 'EntityName', ...props}
                formatted_results.append({
                    "id": entity_data.get("id"),
                    "name": entity_data.get("name", "N/A"),
                    "labels": entity_data.get("types", []),
                    "properties": {k:v for k,v in entity_data.items() if k not in ['id', 'types', 'name']}
                })

            return formatted_results

        except Exception as e:
            logger.exception(f"Error during graph query execution for query '{query}': {e}")
            return [{"error": f"Failed to query graph: {str(e)}"}]

    def close_services(self):
        """Closes underlying services like Neo4j connection."""
        if self.neo4j_service:
            self.neo4j_service.close()
            logger.info("KnowledgeGraphEngine closed Neo4j service.")


# Example Usage (can be removed or moved to a test file)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure Neo4j is running and configured in .env or settings
    # This test assumes the Neo4jRealService and BridgeEntityExtractor work.

    engine = None
    try:
        logger.info("Initializing KnowledgeGraphEngine...")
        engine = KnowledgeGraphEngine()
        logger.info("KnowledgeGraphEngine initialized.")

        # Sample document
        sample_doc_text = """
        金门大桥是一座著名的悬索桥，位于旧金山。该桥的主要结构材料包括钢材和混凝土。
        桥梁的设计规范参考了相关的公路桥涵设计通用规范。施工方法中采用了预制安装技术。
        桥墩基础为桩基。
        """
        doc_name = "金门大桥介绍.txt"

        # Clean up any previous test data for this document to make test idempotent
        # This is a bit tricky as nodes might be shared. For now, we'll just add.
        # A proper cleanup would involve deleting nodes/rels sourced from this doc_name.
        # engine.neo4j_service._execute_query("MATCH (n {source_document: $doc_name}) DETACH DELETE n", {"doc_name": doc_name})
        # logger.info(f"Cleaned up previous data for document: {doc_name}")


        logger.info(f"\n--- Building graph from document: {doc_name} ---")
        build_summary = engine.build_graph_from_document(sample_doc_text, doc_name)
        logger.info(f"Build Summary: {build_summary}")

        assert build_summary["status"] == "Graph construction complete"
        assert build_summary["unique_entities_processed"] > 0
        # Relationship count depends on extraction logic, can be zero if no co-occurrences meet criteria

        logger.info("\n--- Querying graph knowledge: '悬索桥' ---")
        query_results_1 = engine.query_graph_knowledge("悬索桥")
        logger.info(f"Query Results for '悬索桥': {query_results_1}")
        assert len(query_results_1) > 0
        assert any("悬索桥" in r.get("name", "") for r in query_results_1)


        logger.info("\n--- Querying graph knowledge: '钢材' ---")
        query_results_2 = engine.query_graph_knowledge("钢材")
        logger.info(f"Query Results for '钢材': {query_results_2}")
        assert len(query_results_2) > 0
        assert any("钢材" in r.get("name", "") for r in query_results_2)

        logger.info("\n--- Querying graph knowledge: 'non_existent_term_xyz' ---")
        query_results_3 = engine.query_graph_knowledge("non_existent_term_xyz")
        logger.info(f"Query Results for 'non_existent_term_xyz': {query_results_3}")
        assert len(query_results_3) > 0 and query_results_3[0].get("message") # Expecting "no matches" message

        # Test a query that might return multiple related items if search is broad
        logger.info("\n--- Querying graph knowledge: '桥梁' ---") # "桥梁" is generic
        query_results_4 = engine.query_graph_knowledge("桥梁") # Bridge
        logger.info(f"Query Results for '桥梁': {query_results_4}")
        # This might return multiple things or nothing if "桥梁" itself isn't an entity but part of other terms.
        # The current entity extractor would extract "悬索桥", "梁桥", etc.
        # The search_entities is keyword based on 'name'.

        # The current BRIDGE_ENGINEERING_ONTOLOGY has "梁桥" under "桥梁类型"
        # If "金门大桥是一座著名的悬索桥" -> "悬索桥" (桥梁类型)
        # If "该桥的主要结构材料包括钢材和混凝土" -> "钢材", "混凝土" (材料类型)
        # "桥梁的设计规范" -> "公路桥涵设计通用规范" (技术规范)
        # "施工方法中采用了预制安装技术" -> "预制安装" (施工工艺)
        # "桥墩基础为桩基" -> "桥墩", "基础", "桩基" (结构类型)

        # Check if "桩基" (Pile Foundation) was created and can be queried
        logger.info("\n--- Querying graph knowledge: '桩基' ---")
        query_results_5 = engine.query_graph_knowledge("桩基")
        logger.info(f"Query Results for '桩基': {query_results_5}")
        assert len(query_results_5) > 0
        assert any(r.get("name") == "桩基" for r in query_results_5 if isinstance(r, dict))


        logger.info("KnowledgeGraphEngine tests completed.")

    except Exception as e:
        logger.exception(f"Error during KnowledgeGraphEngine testing: {e}")
    finally:
        if engine:
            logger.info("Closing KnowledgeGraphEngine services...")
            engine.close_services()
            logger.info("KnowledgeGraphEngine services closed.")
