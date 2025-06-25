from typing import List, Dict, Any
import random
import hashlib # For basic duplicate detection based on hash

# Placeholder for BridgeEntityExtractor
# from app.services.entity_extraction_service import BridgeEntityExtractor
class BridgeEntityExtractor:
    def __init__(self):
        print("BridgeEntityExtractor initialized (placeholder)")

    def extract_entities(self, text: str) -> List[str]:
        # Placeholder: Simulate entity extraction
        # In a real scenario, this would use NLP techniques
        words = text.lower().split()
        # Example entities - this is highly simplified
        known_bridge_terms = {"bridge", "girder", "pier", "abutment", "deck", "span", "foundation", "cable"}
        return [word for word in words if word in known_bridge_terms]

    def check_term_accuracy(self, term: str) -> bool:
        # Placeholder for checking if a term is a valid/accurate bridge engineering term
        # This could involve a dictionary lookup or a more sophisticated validation
        return term in {"bridge", "girder", "pier", "abutment", "deck", "span", "foundation", "cable", "load", "stress", "concrete", "steel"}


class DataQualityController:
    def __init__(self):
        self.bridge_extractor = BridgeEntityExtractor()
        print("DataQualityController initialized")

    def validate_qa_pairs(self, qa_pairs: List[Dict]) -> Dict:
        """
        Validates the quality of question-answer pairs.
        Checks: question sensibility, answer accuracy (rudimentary), professional terminology.
        Returns a dictionary with validation results (e.g., overall score, issues found).
        """
        print(f"Validating {len(qa_pairs)} QA pairs.")
        results = {"total_pairs": len(qa_pairs), "valid_pairs": 0, "issues": []}
        passed_count = 0

        for i, pair in enumerate(qa_pairs):
            question = pair.get("question", "")
            answer = pair.get("answer", "")
            issue_details = []

            # 1. Question Sensibility (Basic Checks)
            if not question.strip() or not question.endswith("?"):
                issue_details.append("Question is poorly formed or missing.")
            if len(question.split()) < 3: # Arbitrary minimum length
                issue_details.append("Question seems too short or trivial.")

            # 2. Answer Accuracy (Rudimentary - presence of content)
            if not answer.strip():
                issue_details.append("Answer is empty.")
            if len(answer.split()) < 5: # Arbitrary minimum length for a meaningful answer
                issue_details.append("Answer seems too short or incomplete.")

            # 3. Professional Terminology Use (Placeholder)
            # This would involve more sophisticated NLP and domain-specific dictionaries
            question_entities = self.bridge_extractor.extract_entities(question)
            answer_entities = self.bridge_extractor.extract_entities(answer)

            if not question_entities and not answer_entities:
                issue_details.append("No recognizable bridge engineering terms found in Q/A.")
            else:
                # Check if extracted terms are considered "accurate" by the placeholder
                for term in question_entities + answer_entities:
                    if not self.bridge_extractor.check_term_accuracy(term):
                        issue_details.append(f"Term '{term}' might not be accurate or relevant.")
                        break # Stop at first inaccurate term for this pair for simplicity

            if not issue_details:
                passed_count += 1
            else:
                results["issues"].append({"pair_index": i, "question": question, "details": issue_details})

        results["valid_pairs"] = passed_count
        # Simple quality score: percentage of pairs without issues
        results["quality_score"] = (passed_count / len(qa_pairs)) if qa_pairs else 0.0
        print(f"QA validation complete. Score: {results['quality_score']:.2f}")
        return results

    def _calculate_content_hash(self, item: Dict) -> str:
        """Helper to create a hash for a dictionary item for duplicate detection."""
        # Consider only 'question' and 'answer' for QA, or 'description' for entities etc.
        # This is a very basic approach. Real semantic duplicate detection is much harder.
        content_str = ""
        if "question" in item and "answer" in item:
            content_str = str(item.get("question","")) + str(item.get("answer",""))
        elif "description" in item:
            content_str = str(item.get("description",""))
        elif "explanation" in item:
            content_str = str(item.get("explanation",""))
        # For other types, might need to concatenate different fields.
        else: # Fallback: use all string values
            content_str = "".join(str(v) for v in item.values() if isinstance(v, str))

        return hashlib.md5(content_str.encode('utf-8')).hexdigest()


    def filter_duplicate_data(self, data: List[Dict]) -> List[Dict]:
        """
        Removes duplicate data based on content similarity (currently, exact hash of key fields).
        """
        print(f"Filtering duplicates from {len(data)} items.")
        seen_hashes = set()
        unique_data = []
        for item in data:
            item_hash = self._calculate_content_hash(item)
            if item_hash not in seen_hashes:
                unique_data.append(item)
                seen_hashes.add(item_hash)

        print(f"Filtered data: {len(unique_data)} unique items remaining.")
        return unique_data

    def enhance_data_diversity(self, data: List[Dict], target_count: int) -> List[Dict]:
        """
        Enhances data diversity through rewriting and extension (Placeholder).
        This is a complex task that would typically involve LLMs for paraphrasing, etc.
        Current implementation is a placeholder: adds slightly modified copies if under target.
        """
        print(f"Enhancing data diversity for {len(data)} items. Target: {target_count}")
        if len(data) >= target_count:
            print("Current data count meets or exceeds target. No enhancement needed by this basic method.")
            return data

        enhanced_data = list(data) # Start with existing data
        num_to_add = target_count - len(data)

        if not data: # Cannot enhance if no source data
            print("No source data to enhance.")
            return []

        for i in range(num_to_add):
            original_item = random.choice(data) # Pick a random item to "enhance"
            new_item = original_item.copy() # Shallow copy

            # Rudimentary modification (example for QA pairs)
            if "question" in new_item and isinstance(new_item["question"], str):
                new_item["question"] = new_item["question"].replace("What is", "Can you explain") + " (paraphrased)"
            if "answer" in new_item and isinstance(new_item["answer"], str):
                new_item["answer"] = "Essentially, " + new_item["answer"] + " (extended)"
            # For other data types, similar simple modifications would be needed.
            # A real LLM would do proper paraphrasing.

            # Ensure ID is unique if present, or remove it if enhancement means it's a new "version"
            if "id" in new_item:
                new_item["id"] = f"{new_item.get('id', 'item')}_enhanced_{i}"

            enhanced_data.append(new_item)

        print(f"Data enhanced. Total items: {len(enhanced_data)}")
        return enhanced_data

    def score_data_quality(self, data: List[Dict], data_type: str = "generic") -> Dict:
        """
        Scores data quality based on completeness, accuracy (simulated), diversity, professional relevance.
        Returns a dictionary of scores.
        `data_type` can be 'qa', 'entity_description', etc. to apply specific checks.
        """
        print(f"Scoring data quality for {len(data)} items of type '{data_type}'.")
        if not data:
            return {"completeness": 0, "accuracy": 0, "diversity": 0, "professionalism": 0, "overall_score": 0}

        scores = {
            "completeness": 0.0, # Are all required fields present?
            "accuracy": 0.0,     # How correct is the information? (Highly simulated)
            "diversity": 0.0,    # How varied is the data? (Based on unique hashes)
            "professionalism": 0.0 # Relevance to bridge engineering (Simulated by term check)
        }

        # Completeness (Example: check for key fields based on data_type)
        complete_items = 0
        for item in data:
            if data_type == "qa" and item.get("question") and item.get("answer"):
                complete_items +=1
            elif data_type == "entity_description" and item.get("description") and item.get("entity_id"):
                complete_items += 1
            # Add more types as needed
            else: # Generic check: at least one non-empty value
                if any(v for v in item.values()):
                    complete_items +=1
        scores["completeness"] = (complete_items / len(data)) * 5.0 # Scale to 0-5

        # Accuracy (Simulated - for QA, use validation logic; for others, simpler checks)
        if data_type == "qa":
            qa_validation_results = self.validate_qa_pairs(data) # Re-use validation
            scores["accuracy"] = qa_validation_results.get("quality_score", 0.0) * 5.0
        else: # Generic accuracy: assume 70-90% are "accurate" for placeholder
            scores["accuracy"] = random.uniform(3.5, 4.5)

        # Diversity (Based on ratio of unique content hashes)
        # This is a proxy for true semantic diversity.
        if len(data) > 1:
            unique_hashes = set(self._calculate_content_hash(item) for item in data)
            scores["diversity"] = (len(unique_hashes) / len(data)) * 5.0
        else:
            scores["diversity"] = 5.0 # Single item is "fully diverse" in this context

        # Professionalism (Simulated: check for domain-specific terms)
        professional_items = 0
        for item in data:
            text_content = ""
            if data_type == "qa":
                text_content = item.get("question", "") + " " + item.get("answer", "")
            elif data_type == "entity_description":
                text_content = item.get("description", "")
            # ... other types

            if self.bridge_extractor.extract_entities(text_content): # If any domain entity found
                professional_items += 1
        scores["professionalism"] = (professional_items / len(data)) * 5.0 if data else 0.0

        # Overall Score (Simple Average - can be weighted in a real system)
        scores["overall_score"] = sum(scores.values()) / len(scores)

        print(f"Data quality scores: {scores}")
        return scores

    def generate_quality_report(self, quality_scores: Dict) -> str:
        """
        Generates a human-readable quality report from the scores.
        """
        print("Generating quality report.")
        report = "Training Data Quality Report:\n"
        report += "-----------------------------\n"
        for metric, score in quality_scores.items():
            if isinstance(score, float):
                report += f"- {metric.replace('_', ' ').capitalize()}: {score:.2f}/5.0\n"
            else:
                report += f"- {metric.replace('_', ' ').capitalize()}: {score}\n"

        report += "\nSuggestions for Improvement:\n"
        if quality_scores.get("overall_score", 5.0) < 3.0:
            report += "- Overall quality is low. Consider reviewing data generation prompts and sources.\n"
        if quality_scores.get("completeness", 5.0) < 4.0:
            report += "- Completeness is low. Ensure all required data fields are populated.\n"
        if quality_scores.get("accuracy", 5.0) < 3.5: # Assuming 3.5 is a threshold for "good enough"
            report += "- Accuracy needs improvement. Review data for correctness, potentially using human annotators or more advanced validation.\n"
        if quality_scores.get("diversity", 5.0) < 3.0:
            report += "- Diversity is low. Try to generate more varied examples or use data augmentation techniques.\n"
        if quality_scores.get("professionalism", 5.0) < 4.0:
            report += "- Professionalism score suggests data might not be sufficiently domain-specific. Refine generation to focus on bridge engineering topics.\n"

        if quality_scores.get("overall_score", 0) >= 4.0:
             report += "- Overall data quality appears good. Continue monitoring and refining.\n"

        print("Quality report generated.")
        return report

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    controller = DataQualityController()

    # Sample QA data
    sample_qa_data = [
        {"question": "What is a girder bridge?", "answer": "A girder bridge is a bridge that uses girders as the means of supporting its deck."},
        {"question": "Tell me about piers.", "answer": "Piers are vertical supports in a bridge structure."},
        {"question": "What is a girder bridge?", "answer": "A girder bridge is a bridge that uses girders as the means of supporting its deck."}, # Duplicate
        {"question": "How is load distributed?", "answer": "Load is distributed through various structural elements."},
        {"question": "", "answer": "This has no question."}, # Invalid
    ]

    print("\n--- Validating QA Pairs ---")
    validation_res = controller.validate_qa_pairs(sample_qa_data)
    # print(validation_res)

    print("\n--- Filtering Duplicates ---")
    unique_qa_data = controller.filter_duplicate_data(sample_qa_data)
    # print(f"Unique QA data count: {len(unique_qa_data)}")

    print("\n--- Enhancing Data Diversity ---")
    enhanced_data = controller.enhance_data_diversity(unique_qa_data, target_count=5)
    # for item in enhanced_data:
    #     print(item)

    print("\n--- Scoring Data Quality (QA) ---")
    quality_scores_qa = controller.score_data_quality(enhanced_data, data_type="qa")
    # print(quality_scores_qa)

    print("\n--- Generating Quality Report ---")
    report = controller.generate_quality_report(quality_scores_qa)
    print(report)

    # Sample Entity Description Data
    sample_entity_data = [
        {"entity_id": "E1", "description": "A concrete pier supporting the main span."},
        {"entity_id": "E2", "description": "Steel box girder used for long-span bridges."},
        {"entity_id": "E1", "description": "A concrete pier supporting the main span."} # Duplicate
    ]
    print("\n--- Scoring Data Quality (Entity Descriptions) ---")
    quality_scores_entity = controller.score_data_quality(sample_entity_data, data_type="entity_description")
    report_entity = controller.generate_quality_report(quality_scores_entity)
    print(report_entity)
