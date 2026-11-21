from app.services.language import prefers_nepali


def language_rule(text: str) -> str:
    if prefers_nepali(text):
        return "Reply in Nepali."
    return "Reply in English."


def empty_notebook_reply(text: str) -> str:
    if prefers_nepali(text):
        return "यो नोटबुकमा अहिले कुनै कागजात छैन। PDF वा पाठ फाइल राखेर फेरि सोध्नुहोस्।"
    return "This notebook has no documents yet. Upload a PDF or a text file, then ask again."


def missing_source_reply(text: str) -> str:
    if prefers_nepali(text):
        return "यो कुरा यो नोटबुकका कागजातमा भेटिएन।"
    return "I couldn't find that in this notebook."
