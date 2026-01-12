import re
import sys
import json

def verify_and_enforce_citations(answer, metadata_list):
    """
    Verifies that the answer includes page-level citations from the metadata.
    Format: [Annual Report 2024–25, Page {{page_number}}]
    """
    
    # 1. Fallback Rule: If no results found or answer is negative
    if "I could not find this information" in answer or not metadata_list:
        return "I could not find this information in the dataset."

    # 2. Identify claims and citations
    # A simple way to check citations is looking for bracketed page numbers
    citation_pattern = r'\[(?:Annual Report 2024–25, )?Page \d+\]'
    has_citation = re.search(citation_pattern, answer)
    
    # 3. If answer has a generic claim but no citation, append the top metadata's citation
    if not has_citation:
        # Get the primary page from the top retrieval result
        primary_page = metadata_list[0].get("page_number", "N/A")
        if primary_page != "N/A":
            answer = f"{answer.rstrip('.')} [Annual Report 2024–25, Page {primary_page}]."
        else:
            # If no reliable page info, fallback
            return "I could not find this information in the dataset."

    # 4. Final verification: Check if the cited pages actually exist in our retrieved metadata
    cited_pages = re.findall(r'Page (\d+)', answer)
    valid_pages = [str(m.get("page_number")) for m in metadata_list]
    
    # Filter out claims that cite pages we didn't actually retrieve (hallucination check)
    for page in cited_pages:
        if page not in valid_pages:
            # If the model cited a page we didn't provide, it's a hallucination
            return "I could not find this information in the dataset."

    return answer

if __name__ == "__main__":
    # Test cases via CLI
    # Case 1: Answer with missing citation
    # Case 2: Hallucinated citation
    # Case 3: Correct citation
    
    try:
        if len(sys.argv) > 2:
            answer_input = sys.argv[1]
            metadata_input = json.loads(sys.argv[2])
            print(verify_and_enforce_citations(answer_input, metadata_input))
        else:
            # Demo test
            test_answer = "HCLTech's revenue grew by 6.5% in FY25."
            test_metadata = [{"page_number": 11, "doc_title": "HCLTech Annual Report 2024–25"}]
            print("--- CITATION ENFORCEMENT TEST ---")
            print(f"Input: {test_answer}")
            print(f"Output: {verify_and_enforce_citations(test_answer, test_metadata)}")
            
            print("\n--- HALLUCINATION TEST ---")
            hallucinated_answer = "Revenue was 100k [Page 999]"
            print(f"Input: {hallucinated_answer}")
            print(f"Output: {verify_and_enforce_citations(hallucinated_answer, test_metadata)}")
    except Exception as e:
        print(f"Error: {e}")
        print("I could not find this information in the dataset.")
