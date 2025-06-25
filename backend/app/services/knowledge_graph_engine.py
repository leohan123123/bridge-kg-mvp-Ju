from app.services.neo4j_real_service import Neo4jRealService
from app.services.bridge_entity_extractor import BridgeEntityExtractor
from app.services.word_parser_service import WordParserService
from app.services.word_content_analyzer import WordContentAnalyzer
from app.services.drawing_knowledge_extractor import DrawingKnowledgeExtractor # Added for DXF
from app.services.bim_knowledge_builder import BIMKnowledgeBuilder # Added for IFC/BIM
from app.services.ontology_manager import OntologyManager
from app.services.ontology_auto_updater import OntologyAutoUpdater
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
            self.dxf_knowledge_extractor = DrawingKnowledgeExtractor() # Added for DXF
            self.bim_knowledge_builder = BIMKnowledgeBuilder() # Added for IFC/BIM
            self.ontology_manager = OntologyManager()
            self.ontology_auto_updater = OntologyAutoUpdater() # Uses OntologyManager and BridgeEntityExtractor
        except Exception as e:
            logger.error(f"Failed to initialize services in KnowledgeGraphEngine: {e}")
            raise
        # BridgeEntityExtractor is used by WordContentAnalyzer, build_graph_from_document, and OntologyAutoUpdater.
        # WordContentAnalyzer has its own instance. OntologyAutoUpdater also has its own.
        # For build_graph_from_document, we use self.entity_extractor.
        self.entity_extractor = BridgeEntityExtractor() # Used for text-based entity extraction


    def build_graph_with_ontology_update(self, file_path: str, document_name: str, file_type: str, auto_update_ontology: bool = True, text_content: str = None) -> Dict:
        """
        Builds a knowledge graph from a given file (Word, DXF, IFC, or plain text)
        and incorporates ontology update mechanisms.

        Args:
            file_path (str): Path to the document file.
            document_name (str): Name of the document.
            file_type (str): Type of the file ('word', 'dxf', 'ifc', 'text').
            auto_update_ontology (bool): If True, attempts to automatically apply high-confidence ontology updates.
                                         If False, only suggests updates.
            text_content (str, optional): For 'text' file_type, the actual text content. Required if file_type is 'text'.

        Returns:
            Dict: A summary of the graph building process, including ontology update actions.
        """
        logger.info(f"Starting graph construction with ontology update for: {document_name} (Type: {file_type}, Auto-update: {auto_update_ontology})")

        processing_summary = {}
        extracted_entities_for_ontology_update = None # This will hold data for suggest_ontology_updates

        if file_type == 'word':
            # Process Word document, extract text, and build initial graph
            # build_graph_from_word_document itself calls build_graph_from_document for text part
            # We need to get the core text for ontology update suggestions.
            parsed_word_content = self.word_parser_service.extract_text_content(file_path)
            core_text = parsed_word_content.get("text")
            if not core_text:
                logger.error(f"No text content extracted from Word file: {file_path}")
                return {"status": "Error", "message": "No text from Word file for ontology update."}

            # The build_graph_from_word_document will handle graph creation from various parts of Word doc.
            # For ontology update, we primarily use the main textual content.
            processing_summary = self.build_graph_from_word_document(file_path, document_name)
            # OntologyAutoUpdater's BridgeEntityExtractor will re-process this text.
            # Alternatively, pass entities from WordContentAnalyzer if its extraction is preferred.
            # For now, let OntologyAutoUpdater use its own extractor on the core_text.
            extracted_entities_for_ontology_update = self.ontology_auto_updater.bridge_extractor.extract_entities_from_text(core_text)

        elif file_type == 'dxf':
            processing_summary = self.build_graph_from_dxf_drawing(file_path, document_name)
            # For DXF, ontology update might be based on new layer names, block names, text entities, etc.
            # This requires specific logic in DrawingKnowledgeExtractor or a dedicated mapper.
            # For now, we'll assume no direct ontology update suggestions from DXF structure in this MVP.
            # Or, if DrawingKnowledgeExtractor produces text, use that.
            # Placeholder:
            logger.info("Ontology update from DXF structure is not yet fully implemented. Graph built from DXF.")
            extracted_entities_for_ontology_update = None # Or extract from DXF text if available

        elif file_type == 'ifc':
            processing_summary = self.build_graph_from_bim_model(file_path, document_name)
            # For IFC, new IfcEntity types or property names could be ontology update candidates.
            # BIMKnowledgeBuilder's output (nodes with types/properties) could be analyzed.
            # Placeholder:
            logger.info("Ontology update from IFC structure is not yet fully implemented. Graph built from IFC.")
            kg_data_from_bim = self.bim_knowledge_builder.build_knowledge_from_bim(file_path) # Re-extract or get from summary

            # Simplistic approach: treat new IFC types or properties as suggestions
            # This needs a more refined mapping to what constitutes an "ontology update suggestion"
            # For now, we'll simulate this or leave it for future enhancement.
            # Example: if kg_data_from_bim['nodes'] contains a node with a type not in ontology.
            # This part is complex and needs careful design.
            extracted_entities_for_ontology_update = None # Placeholder

        elif file_type == 'text':
            if not text_content:
                logger.error("Text content must be provided for file_type 'text'.")
                return {"status": "Error", "message": "Text content required for 'text' type."}
            processing_summary = self.build_graph_from_document(text_content, document_name)
            extracted_entities_for_ontology_update = self.ontology_auto_updater.bridge_extractor.extract_entities_from_text(text_content)

        else:
            logger.error(f"Unsupported file type for graph building: {file_type}")
            return {"status": "Error", "message": f"Unsupported file type: {file_type}"}

        # --- Ontology Update Steps (Common for text-based content) ---
        ontology_update_actions = {
            "suggestions_made": None,
            "gaps_detected": None,
            "auto_update_result": None,
            "report": ""
        }

        if extracted_entities_for_ontology_update:
            logger.info(f"Suggesting ontology updates for {document_name}...")
            suggestions = self.ontology_auto_updater.suggest_ontology_updates(extracted_entities_for_ontology_update)
            ontology_update_actions["suggestions_made"] = suggestions

            report = self.ontology_auto_updater.generate_update_report(suggestions)
            ontology_update_actions["report"] = report
            logger.info(f"Ontology Update Report for {document_name}:\n{report}")

            if auto_update_ontology and suggestions and any(suggestions.values()):
                logger.info(f"Attempting to auto-expand ontology for {document_name}...")
                # Using a default confidence, or it could be configurable
                expansion_result = self.ontology_auto_updater.auto_expand_ontology(suggestions, confidence_threshold=0.8)
                ontology_update_actions["auto_update_result"] = expansion_result
                logger.info(f"Ontology auto-expansion result for {document_name}: {expansion_result}")
            else:
                logger.info(f"Auto-update for ontology is disabled or no suggestions made for {document_name}.")

        # Combine graph building summary with ontology update actions
        final_summary = {
            "graph_building_summary": processing_summary,
            "ontology_update_actions": ontology_update_actions,
            "document_name": document_name,
            "overall_status": "Processing complete with ontology update considerations."
        }

        return final_summary


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


    def build_graph_from_dxf_drawing(self, file_path: str, document_name: str) -> Dict:
        """
        Builds a knowledge graph from a DXF drawing file.
        1. Extracts knowledge using DrawingKnowledgeExtractor.
        2. Creates nodes and relationships in Neo4j based on the extracted knowledge graph structure.
        Returns a summary of the build process.
        """
        logger.info(f"Starting graph construction from DXF drawing: {document_name} at {file_path}")
        try:
            # 1. Extract knowledge from DXF
            # The DrawingKnowledgeExtractor returns a dict with 'knowledge_graph': {'nodes': [], 'edges': []}
            extracted_data = self.dxf_knowledge_extractor.extract_knowledge_from_drawing(file_path)

            if extracted_data.get("error"):
                logger.error(f"Error extracting knowledge from DXF {document_name}: {extracted_data['error']}")
                return {
                    "status": "Error: Failed to extract knowledge from DXF",
                    "document_name": document_name, "error": extracted_data['error'],
                    "nodes_created": 0, "rels_created": 0
                }

            kg_data = extracted_data.get("knowledge_graph")
            if not kg_data or not kg_data.get("nodes"):
                logger.warning(f"No graph nodes extracted from DXF document: {document_name}")
                return {
                    "status": "No graph nodes extracted from DXF", "document_name": document_name,
                    "nodes_created": 0, "rels_created": 0
                }

            nodes_to_create = kg_data["nodes"]
            edges_to_create = kg_data.get("edges", [])

            created_node_neo4j_ids = {}  # Map internal ID from extractor to Neo4j element ID
            nodes_created_count = 0
            rels_created_count = 0

            # 2. Create nodes in Neo4j
            for node_data in nodes_to_create:
                internal_id = node_data.pop("id") # Extractor's internal ID for linking edges
                node_type = node_data.pop("type", "DrawingElement") # Default type if not specified
                label = node_data.pop("label", None) # Primary display name

                properties = {**node_data} # Remaining items are properties
                if label:
                    properties["name"] = label # Use 'label' as 'name' if present, a common convention

                properties["source_document"] = document_name
                properties["source_file_path"] = file_path # Add file path for drawing entities

                # Use neo4j_service to create the node. It expects entity_type (as label) and properties.
                # The create_bridge_entity method returns the element_id of the created node.
                neo4j_element_id = self.neo4j_service.create_bridge_entity(
                    entity_type=node_type, # This will be the primary label in Neo4j
                    properties=properties
                )

                if neo4j_element_id:
                    created_node_neo4j_ids[internal_id] = neo4j_element_id
                    nodes_created_count += 1
                    logger.debug(f"Created DXF node: {label or node_type} (InternalID: {internal_id}) with Neo4j ElemID: {neo4j_element_id}")
                else:
                    logger.error(f"Failed to create DXF node in Neo4j: {label or node_type} (InternalID: {internal_id})")

            logger.info(f"Created {nodes_created_count} nodes from DXF: {document_name}")

            # 3. Create relationships in Neo4j
            if edges_to_create:
                for edge_data in edges_to_create:
                    source_internal_id = edge_data.get("source")
                    target_internal_id = edge_data.get("target")
                    rel_type = edge_data.get("label", "RELATED_TO").upper().replace(" ", "_")

                    rel_properties = {k:v for k,v in edge_data.items() if k not in ["source", "target", "label"]}
                    rel_properties["source_document"] = document_name

                    source_neo4j_id = created_node_neo4j_ids.get(source_internal_id)
                    target_neo4j_id = created_node_neo4j_ids.get(target_internal_id)

                    if source_neo4j_id and target_neo4j_id:
                        success = self.neo4j_service.create_relationship_by_element_ids(
                            start_node_element_id=source_neo4j_id,
                            end_node_element_id=target_neo4j_id,
                            rel_type=rel_type,
                            properties=rel_properties
                        )
                        if success:
                            rels_created_count += 1
                            logger.debug(f"Created DXF relationship: ({source_internal_id})-[{rel_type}]->({target_internal_id})")
                        else:
                            logger.error(f"Failed to create DXF relationship: ({source_internal_id})-[{rel_type}]->({target_internal_id})")
                    else:
                        logger.warning(f"Skipping DXF relationship due to missing Neo4j node ID(s): {source_internal_id} -> {target_internal_id}")

            logger.info(f"Created {rels_created_count} relationships from DXF: {document_name}")

            return {
                "status": "DXF Graph construction complete",
                "document_name": document_name,
                "file_path": file_path,
                "document_info_from_dxf": extracted_data.get("document_info"),
                "analysis_summary_from_dxf": extracted_data.get("analysis_summary"),
                "nodes_created": nodes_created_count,
                "rels_created": rels_created_count,
            }

        except Exception as e:
            logger.exception(f"Error building graph from DXF drawing {document_name} at {file_path}: {e}")
            return {
                "status": "Error during DXF graph construction",
                "document_name": document_name,
                "file_path": file_path,
                "error": str(e),
                "nodes_created": 0,
                "rels_created": 0
            }

    def build_graph_from_bim_model(self, file_path: str, document_name: str) -> Dict:
        """
        Builds a knowledge graph from a BIM (IFC) model file.
        1. Extracts knowledge (nodes and relationships) using BIMKnowledgeBuilder.
        2. Creates these nodes and relationships in Neo4j.
        Returns a summary of the build process.
        """
        logger.info(f"Starting graph construction from BIM model: {document_name} at {file_path}")
        try:
            # 1. Extract knowledge from BIM using BIMKnowledgeBuilder
            # The builder returns a dict with 'nodes': [] and 'relationships': []
            kg_data_from_builder = self.bim_knowledge_builder.build_knowledge_from_bim(file_path)

            if kg_data_from_builder.get("error"):
                logger.error(f"Error extracting knowledge from BIM {document_name}: {kg_data_from_builder['error']}")
                return {
                    "status": "Error: Failed to extract knowledge from BIM model",
                    "document_name": document_name, "error": kg_data_from_builder['error'],
                    "nodes_created_in_db": 0, "rels_created_in_db": 0
                }

            nodes_to_create = kg_data_from_builder.get("nodes", [])
            relationships_to_create = kg_data_from_builder.get("relationships", [])

            if not nodes_to_create:
                logger.warning(f"No graph nodes extracted from BIM model: {document_name}")
                return {
                    "status": "No graph nodes extracted from BIM model", "document_name": document_name,
                    "nodes_created_in_db": 0, "rels_created_in_db": 0
                }

            created_node_neo4j_ids = {}  # Map internal ID from builder to Neo4j element ID
            nodes_created_count = 0
            rels_created_count = 0

            # 2. Create nodes in Neo4j
            for node_data in nodes_to_create:
                # BIMKnowledgeBuilder provides 'id', 'type', 'label', 'properties'
                internal_id = node_data.get("id") # Builder's ID for linking relationships
                node_type = node_data.get("type", "BimElement") # Primary label for Neo4j
                label_prop = node_data.get("label", internal_id) # Used as 'name' property

                properties = node_data.get("properties", {})
                # Ensure 'name' property exists, using label_prop as primary source
                if 'name' not in properties or not properties['name']:
                    properties["name"] = label_prop

                properties["internal_id_from_source"] = internal_id # Store original ID for reference
                properties["source_document_type"] = "BIM/IFC"
                properties["source_document_name"] = document_name
                properties["source_file_path"] = file_path

                neo4j_element_id = self.neo4j_service.create_bridge_entity(
                    entity_type=node_type,
                    properties=properties
                )

                if neo4j_element_id:
                    created_node_neo4j_ids[internal_id] = neo4j_element_id
                    nodes_created_count += 1
                    logger.debug(f"Created BIM node: {properties.get('name', node_type)} (InternalID: {internal_id}) with Neo4j ElemID: {neo4j_element_id}")
                else:
                    logger.error(f"Failed to create BIM node in Neo4j: {properties.get('name', node_type)} (InternalID: {internal_id})")

            logger.info(f"Created {nodes_created_count} nodes from BIM model: {document_name}")

            # 3. Create relationships in Neo4j
            if relationships_to_create:
                for rel_data in relationships_to_create:
                    source_internal_id = rel_data.get("source")
                    target_internal_id = rel_data.get("target")
                    rel_type = rel_data.get("type", "RELATED_TO").upper().replace(" ", "_").replace("-","_") # Sanitize

                    rel_properties = rel_data.get("properties", {})
                    rel_properties["source_document_name"] = document_name

                    source_neo4j_id = created_node_neo4j_ids.get(source_internal_id)
                    target_neo4j_id = created_node_neo4j_ids.get(target_internal_id)

                    if source_neo4j_id and target_neo4j_id:
                        if source_neo4j_id == target_neo4j_id:
                            logger.warning(f"Skipping self-referential BIM relationship for node {source_internal_id} (Neo4j ID: {source_neo4j_id}) of type {rel_type}")
                            continue

                        success = self.neo4j_service.create_relationship_by_element_ids(
                            start_node_element_id=source_neo4j_id,
                            end_node_element_id=target_neo4j_id,
                            rel_type=rel_type,
                            properties=rel_properties
                        )
                        if success:
                            rels_created_count += 1
                        else:
                            logger.error(f"Failed to create BIM relationship: ({source_internal_id})-[{rel_type}]->({target_internal_id}) with Neo4j IDs {source_neo4j_id} -> {target_neo4j_id}")
                    else:
                        missing_ids_info = []
                        if not source_neo4j_id: missing_ids_info.append(f"Source '{source_internal_id}' (Neo4j ID unknown)")
                        if not target_neo4j_id: missing_ids_info.append(f"Target '{target_internal_id}' (Neo4j ID unknown)")
                        logger.warning(f"Skipping BIM relationship of type {rel_type} due to missing Neo4j node ID(s): {' '.join(missing_ids_info)}")

            logger.info(f"Created {rels_created_count} relationships from BIM model: {document_name}")

            return {
                "status": "BIM Model Graph construction complete",
                "document_name": document_name,
                "file_path": file_path,
                "nodes_created_in_db": nodes_created_count,
                "rels_created_in_db": rels_created_count,
                "summary_from_builder": {
                    "nodes_identified_by_builder": len(nodes_to_create),
                    "rels_identified_by_builder": len(relationships_to_create)
                }
            }

        except Exception as e:
            logger.exception(f"Error building graph from BIM model {document_name} at {file_path}: {e}")
            return {
                "status": "Error during BIM model graph construction",
                "document_name": document_name,
                "file_path": file_path,
                "error": str(e),
                "nodes_created_in_db": 0,
                "rels_created_in_db": 0
            }

    def close_services(self):
        """Closes underlying services like Neo4j connection."""
        if self.neo4j_service:
            self.neo4j_service.close()
            logger.info("KnowledgeGraphEngine closed Neo4j service.")

    def auto_generate_training_data(self, graph_stats: Dict, auto_export: bool = False) -> Dict:
        """
        Graph construction完成后自动生成训练数据.
        1. 分析图谱内容 (based on graph_stats and potentially more queries).
        2. 生成对应的训练数据 (e.g., QA pairs, entity descriptions).
        3. 质量控制和优化.
        4. 可选自动导出.
        """
        logger.info(f"Starting automatic training data generation. Graph stats: {graph_stats}, Auto-export: {auto_export}")

        # Initialize services needed for training data generation
        # These should ideally be injected or available if KGE is part of a larger app context
        # For now, direct instantiation if not already members.
        # To avoid circular dependencies if these services use KGE, they should be independent or use facades.
        try:
            # Assuming these are importable from the current service layer
            from .training_data_generator import TrainingDataGenerator
            from .data_quality_controller import DataQualityController
            from .data_export_service import DataExportService
        except ImportError:
            logger.error("Failed to import training data services for auto-generation. Ensure they are in the same services package.")
            # Fallback to placeholders if actual services can't be imported (e.g. during isolated testing or if structure is different)
            # This section is for robustness in case the primary import fails due to pathing or circularity in some contexts.
            # In a well-structured FastAPI app with dependency injection, this wouldn't be needed.
            logger.warning("Falling back to placeholder training data services for auto_generate_training_data.")
            class TrainingDataGeneratorPlaceholder:
                def generate_qa_pairs_from_graph(self, entity_types: List[str] = None, limit: int = 10) -> List[Dict]: return [{"question": "Placeholder Q", "answer": "Placeholder A"}]
                def generate_entity_descriptions(self, entity_types: List[str], limit: int = 5) -> List[Dict]: return [{"entity_id": "ph_id", "description":"Placeholder desc"}]
            class DataQualityControllerPlaceholder:
                def score_data_quality(self, data: List[Dict], data_type: str = "generic") -> Dict: return {"overall_score": 3.0}
                def generate_quality_report(self, quality_scores: Dict) -> str: return "Placeholder quality report."
            class DataExportServicePlaceholder:
                def __init__(self, output_dir="auto_exports_kge"):
                    self.output_dir = output_dir
                    if not os.path.exists(output_dir): os.makedirs(output_dir)
                def create_export_package(self, export_config: Dict) -> Dict:
                    pkg_loc = os.path.join(self.output_dir, export_config.get("package_name", "pkg"))
                    os.makedirs(pkg_loc, exist_ok=True)
                    return {"package_location": pkg_loc, "files_generated": ["dummy.txt"], "metadata": {}}

            data_generator = TrainingDataGeneratorPlaceholder()
            quality_controller = DataQualityControllerPlaceholder()
            export_service = DataExportServicePlaceholder()
        else: # If imports succeed
            data_generator = TrainingDataGenerator()
            quality_controller = DataQualityController()
            export_service = DataExportService() # Initialize with default export path or configure

        generation_summary = {}
        all_generated_data = {} # To store data of different types

        # 1. Analyze graph content (graph_stats provides some info)
        # We might decide which types of data to generate based on stats
        # e.g., if many entities of type 'Bridge' exist, generate descriptions for them.
        # For MVP, let's try to generate a mix: QA pairs and entity descriptions.

        num_entities = graph_stats.get("unique_entities_processed", graph_stats.get("nodes_created", 0))
        target_qa_pairs = min(max(50, num_entities // 2), 500) # Generate some QA pairs, capped
        target_entity_descriptions = min(max(20, num_entities // 5), 200) # And some descriptions

        # 2. Generate training data
        logger.info(f"Generating {target_qa_pairs} QA pairs...")
        try:
            # Determine relevant entity types from graph_stats if possible, or use generic ones
            # graph_stats might have entities_found_by_category: {"Bridge": 10, "Pier": 20}
            entity_types_for_qa = list(graph_stats.get("entities_found_by_category", {}).keys())[:3] # Use top 3 for variety
            if not entity_types_for_qa: entity_types_for_qa = None # Default to generator's internal logic

            qa_pairs = data_generator.generate_qa_pairs_from_graph(entity_types=entity_types_for_qa, limit=target_qa_pairs)
            all_generated_data["qa_pairs"] = qa_pairs
            generation_summary["qa_pairs_generated"] = len(qa_pairs)
            logger.info(f"Generated {len(qa_pairs)} QA pairs.")
        except Exception as e:
            logger.error(f"Error generating QA pairs: {e}")
            generation_summary["qa_pairs_error"] = str(e)

        logger.info(f"Generating {target_entity_descriptions} entity descriptions...")
        try:
            # Use entity types that are prominent in the graph
            entity_types_for_desc = list(graph_stats.get("entities_found_by_category", {}).keys())[:5] # Describe top 5 types
            if not entity_types_for_desc:
                 # If no types from stats, maybe pick common bridge engineering types as a fallback
                 entity_types_for_desc = ["Bridge", "Beam", "Column", "Foundation"] # Example defaults

            # Ensure entity_types_for_desc is not empty if generator requires it
            if entity_types_for_desc:
                entity_descriptions = data_generator.generate_entity_descriptions(entity_types=entity_types_for_desc, limit=target_entity_descriptions)
                all_generated_data["entity_descriptions"] = entity_descriptions
                generation_summary["entity_descriptions_generated"] = len(entity_descriptions)
                logger.info(f"Generated {len(entity_descriptions)} entity descriptions.")
            else:
                logger.warning("No specific entity types identified for generating descriptions. Skipping.")
                generation_summary["entity_descriptions_generated"] = 0

        except Exception as e:
            logger.error(f"Error generating entity descriptions: {e}")
            generation_summary["entity_descriptions_error"] = str(e)

        # 3. Quality control and optimization
        quality_reports = {}
        for data_type, data_items in all_generated_data.items():
            if data_items:
                logger.info(f"Performing quality control for {data_type}...")
                try:
                    quality_scores = quality_controller.score_data_quality(data_items, data_type=data_type)
                    report_str = quality_controller.generate_quality_report(quality_scores)
                    quality_reports[data_type] = {
                        "scores": quality_scores,
                        "report_summary": report_str.split('\n')[0] # First line as summary
                    }
                    logger.info(f"Quality assessment for {data_type}: Score {quality_scores.get('overall_score')}")
                except Exception as e:
                    logger.error(f"Error during quality control for {data_type}: {e}")
                    quality_reports[data_type] = {"error": str(e)}
            else:
                logger.info(f"No data for {data_type} to perform quality control on.")


        generation_summary["quality_assessments"] = quality_reports

        # 4. Optional auto-export
        if auto_export and all_generated_data:
            logger.info("Auto-exporting generated training data...")
            export_results = {}
            for data_type, data_items in all_generated_data.items():
                if data_items:
                    try:
                        export_config = {
                            "data_type": data_type,
                            "generation_params": {"source": "auto_generated_from_graph", "original_graph_stats": graph_stats},
                            "export_formats": ["jsonl", "csv"], # Default formats for auto-export
                            "package_name": f"auto_export_{data_type}_{graph_stats.get('document_name', 'generic_graph').replace('.', '_')}_{uuid.uuid4().hex[:8]}"
                        }
                        # The export service's create_export_package expects the data to be generated by ITSELF.
                        # Here, we have pre-generated data. We need a way to pass this data to the export service,
                        # or the export service needs a method to export pre-existing data.
                        # For now, let's assume DataExportService might need adjustment or we use its internal generation
                        # based on simplified params.
                        # OR, more practically, the DataExportService should have methods like:
                        # export_service.export_data(data_items, format, path) and then package these.
                        # Given the current DataExportService.create_export_package, it RE-GENERATES data.
                        # This is not ideal for this flow.
                        #
                        # Workaround: For now, we'll log that export would happen and what would be exported.
                        # A real implementation would require DataExportService to handle pre-generated data.
                        logger.info(f"Simulating export for {data_type}. Package config: {export_config['package_name']}")
                        # Actual call would be:
                        # package_info = export_service.create_export_package(export_config)
                        # This would re-generate if not careful.
                        # Let's assume for this placeholder that create_export_package can be "told" what data to use,
                        # or it's smart enough. The current placeholder for DataExportService in KGE does re-generate.
                        # This needs refinement in the actual service interaction.

                        # TEMPORARY: To make the placeholder flow, we'll call the placeholder export
                        # which does its own mini-generation. This is not ideal but makes the code run.
                        # A better approach: DataExportService.export_prepared_data_package(data_items, export_config)

                        # Using the existing placeholder structure, which implies re-generation or simplified generation:
                        # This part highlights a design consideration for service interaction.
                        # For now, the placeholder data_export_service.create_export_package will run its own logic.
                        # The "data_items" we generated above are effectively just for quality check in this temporary setup.

                        # Let's assume the `export_config` can somehow signal to use the data in `data_items`
                        # or, more realistically, the `DataExportService` is refactored.
                        # Since `export_service` here might be the placeholder, its `create_export_package` is simple.
                        # If it's the real one, it would trigger its own generation.

                        # Let's make the export_config for the placeholder explicit about generation:
                        placeholder_export_config = {
                             "data_type": data_type,
                             "generation_params": {"limit": len(data_items)}, # Try to match length
                             "export_formats": ["jsonl", "csv"],
                             "package_name": f"auto_export_{data_type}_{graph_stats.get('document_name', 'graph').replace('.', '_')}_{uuid.uuid4().hex[:8]}"
                        }
                        # This is if export_service is the placeholder from above.
                        # If it's the REAL service, it would use its TrainingDataGenerator.
                        # Corrected call to pass pre-generated data:
                        package_info = export_service.create_export_package(
                            export_config=export_config, # Use the original export_config
                            data_to_export=data_items
                        )

                        export_results[data_type] = {
                            "package_location": package_info.get("package_location"),
                            "files": package_info.get("files_generated")
                        }
                        logger.info(f"Auto-exported {data_type} to {package_info.get('package_location')}")
                    except Exception as e:
                        logger.error(f"Error auto-exporting {data_type}: {e}")
                        export_results[data_type] = {"error": str(e)}
            generation_summary["auto_export_results"] = export_results
        else:
            logger.info("Auto-export disabled or no data to export.")

        logger.info("Automatic training data generation process finished.")
        return generation_summary


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

        # Test DXF processing
        # Create a dummy DXF file for testing
        temp_dxf_path = "temp_kg_engine_test.dxf"
        # Conditional import of ezdxf for testing
        try:
            import ezdxf
            ezdxf_available = True
        except ImportError:
            ezdxf_available = False
            logger.warning("ezdxf library not found, DXF processing test in __main__ will be limited or skipped.")

        if ezdxf_available:
            try:
                test_doc = ezdxf.new('R2010')
                test_msp = test_doc.modelspace()
                test_doc.layers.new(name='CONCRETE_PARTS', dxfattribs={'color': 3})
                test_msp.add_line((0,0), (5,5), dxfattribs={'layer': 'CONCRETE_PARTS'})
                test_msp.add_text('Concrete Beam Section', dxfattribs={'insert': (1,1), 'layer': 'TEXTLAYER'}) # Example text
                test_doc.saveas(temp_dxf_path)

                logger.info(f"\n--- Building graph from DXF document with ontology update: {temp_dxf_path} ---")
                # For DXF, ontology update might be based on text entities or new layer/block names.
                # The current `build_graph_with_ontology_update` for DXF is mostly a placeholder for ontology part.
                dxf_build_summary_with_ontology = engine.build_graph_with_ontology_update(
                    file_path=temp_dxf_path,
                    document_name=os.path.basename(temp_dxf_path),
                    file_type='dxf',
                    auto_update_ontology=False # Don't auto-apply for this test
                )
                logger.info(f"DXF Build Summary with Ontology: {dxf_build_summary_with_ontology}")
                assert dxf_build_summary_with_ontology["graph_building_summary"]["status"] == "DXF Graph construction complete"
                assert dxf_build_summary_with_ontology["graph_building_summary"]["nodes_created"] > 0
                # Check if ontology suggestions were attempted (even if none made for DXF yet)
                assert "suggestions_made" in dxf_build_summary_with_ontology["ontology_update_actions"]


            except Exception as e:
                logger.error(f"Error during DXF processing test: {e}")
            finally:
                if os.path.exists(temp_dxf_path):
                    os.remove(temp_dxf_path)
        else: # ezdxf not available
             logger.info("Skipping DXF part of __main__ test as ezdxf is not installed.")


        # Test build_graph_with_ontology_update with text content
        logger.info(f"\n--- Building graph from text with ontology update: {doc_name} (auto_update=True) ---")
        # This will use the same sample_doc_text
        # This time, let's try with auto_update_ontology = True
        # Note: The OntologyManager mock needs to be stateful for auto-updates to be reflected in subsequent get_ontology_structure calls.
        # The current OntologyManager's Neo4jRealService mock is static regarding schema updates.
        # So, auto_expand_ontology will print what it *would* do.
        text_build_summary_auto_update = engine.build_graph_with_ontology_update(
            file_path=None, # Not used for 'text' type if content is provided
            document_name=doc_name + "_with_auto_ontology_update",
            file_type='text',
            text_content=sample_doc_text,
            auto_update_ontology=True
        )
        logger.info(f"Text Build Summary with Auto Ontology Update: {text_build_summary_auto_update}")
        assert text_build_summary_auto_update["overall_status"] == "Processing complete with ontology update considerations."
        assert text_build_summary_auto_update["graph_building_summary"]["status"] == "Graph construction complete"
        assert "auto_update_result" in text_build_summary_auto_update["ontology_update_actions"]
        # If suggestions were made, auto_update_result should not be None.
        # Example: if "钢筋混凝土" was a new entity type suggestion, auto_expand would attempt to add it.
        # The `ontology_auto_updater.auto_expand_ontology` prints messages like "Attempting to add entity type..."

        logger.info("KnowledgeGraphEngine tests completed.")

    except Exception as e:
        logger.exception(f"Error during KnowledgeGraphEngine testing: {e}")
    finally:
        if engine:
            logger.info("Closing KnowledgeGraphEngine services...")
            engine.close_services()
            logger.info("KnowledgeGraphEngine services closed.")
