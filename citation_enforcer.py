import re

import sys

import json

def verify_and_enforce_citations(answer, metadata_list):

                                                                                   

    if "I could not find this information" in answer or not metadata_list:

        return "I could not find this information in the dataset."

    citation_pattern = r'\[(?:Annual Report 2024–25, )?Page \d+\]'

    has_citation = re.search(citation_pattern, answer)

    

    if not has_citation:

        primary_page = metadata_list[0].get("page_number", "N/A")

        if primary_page != "N/A":

            answer = f"{answer.rstrip('.')} [Annual Report 2024–25, Page {primary_page}]."

        else:

            return "I could not find this information in the dataset."

                                                                    

    valid_pages = [str(m.get("page_number")) for m in metadata_list]

    

                                                                                

    def citation_cleaner(match):

        citation = match.group(0)

        page_match = re.search(r'Page (\d+)', citation)

        if page_match and page_match.group(1) in valid_pages:

            return citation

        return ""                          

    answer = re.sub(r'\[(?:Annual Report 2024–25, )?Page \d+\]', citation_cleaner, answer)

    answer = re.sub(r'\s+', ' ', answer).strip()

    

                                                        

    if not re.search(citation_pattern, answer):

        primary_page = metadata_list[0].get("page_number", "N/A")

        answer = f"{answer.rstrip('.')} [Annual Report 2024–25, Page {primary_page}]."

    return answer

if __name__ == "__main__":

    try:

        if len(sys.argv) > 2:

            answer_input = sys.argv[1]

            metadata_input = json.loads(sys.argv[2])

            print(verify_and_enforce_citations(answer_input, metadata_input))

        else:

            test_answer = "HCLTech's revenue grew by 6.5% in FY25."

            test_metadata = [{"page_number": 11, "doc_title": "HCLTech Annual Report 2024–25"}]

            print(f"Output: {verify_and_enforce_citations(test_answer, test_metadata)}")

            

            hallucinated_answer = "Revenue was 100k [Page 999]"

            print(f"Output: {verify_and_enforce_citations(hallucinated_answer, test_metadata)}")

    except Exception as e:

        print("I could not find this information in the dataset.")

