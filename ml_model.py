# ml_model.py

from collections import Counter

def get_most_reflected_style(selected_styles):
    style_counter = Counter(selected_styles)
    return style_counter.most_common(1)[0][0]

def analyze_overall_style_preference(outfits):
    all_styles = [outfit.style for outfit in outfits]
    style_counter = Counter(all_styles)
    most_frequent_style = style_counter.most_common(1)[0][0] if style_counter else None

    all_items = [item for outfit in outfits for item in outfit.items]
    item_counter = Counter(item['File path'] for item in all_items)
    most_frequent_image = item_counter.most_common(1)[0][0] if item_counter else None

    return most_frequent_style, most_frequent_image

