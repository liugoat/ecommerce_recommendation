"""
Unified recommendation entrypoints.
"""
from typing import Dict, List, Optional

from database.db_utils import get_user_behaviors


def get_recommendations(
    user_id: Optional[int] = None,
    product_id: Optional[int] = None,
    top_n: int = 10,
    db_path: str = "ecommerce.db",
) -> List[Dict]:
    """Single recommendation API.

    - `product_id` provided: similar items recommendation
    - `user_id` absent: popular recommendation
    - `user_id` present: collaborative recommendation with fallback to popular
    """
    if product_id is not None:
        from recommendation.content_based import recommend_similar_products
        from data_processing.feature_engineering import build_feature_matrix
        from database.db_utils import query_all_products

        all_products = query_all_products(db_path)
        if not all_products:
            return []

        feature_matrix, _ = build_feature_matrix(all_products)
        return recommend_similar_products(product_id, feature_matrix, top_n, db_path)

    if user_id is None:
        from recommendation.popularity import get_popular_recommendations

        return get_popular_recommendations(top_n, db_path)

    user_behaviors = get_user_behaviors(user_id, db_path)
    if not user_behaviors:
        from recommendation.popularity import get_popular_recommendations

        return get_popular_recommendations(top_n, db_path)

    from recommendation.collaborative import recommend_by_user

    collaborative_recs = recommend_by_user(user_id, top_n, db_path)
    if collaborative_recs:
        return collaborative_recs

    from recommendation.popularity import get_popular_recommendations

    return get_popular_recommendations(top_n, db_path)


def get_homepage_recommendations(
    user_id: Optional[int] = None,
    top_n: int = 10,
    db_path: str = "ecommerce.db",
) -> Dict[str, List[Dict]]:
    """Return recommendation bundles for homepage sections."""
    from recommendation.popularity import get_popular_recommendations, get_new_arrivals

    popular = get_popular_recommendations(top_n, db_path)
    new_arrivals = get_new_arrivals(top_n, db_path)

    # Fallback for datasets without crawl_time.
    if not new_arrivals:
        from database.db_utils import query_all_products

        all_products = query_all_products(db_path)
        all_products.sort(key=lambda x: x.get("id") or 0, reverse=True)
        new_arrivals = all_products[:top_n]

    personalized = (
        get_recommendations(user_id=user_id, top_n=top_n, db_path=db_path)
        if user_id is not None
        else popular
    )

    seed_list = personalized or popular
    similar = []
    if seed_list:
        seed_product = seed_list[0]
        seed_product_id = seed_product.get("id")
        if seed_product_id is not None:
            similar = get_recommendations(product_id=seed_product_id, top_n=top_n, db_path=db_path)

    if not similar:
        similar = popular[:top_n]

    return {
        "popular": popular,
        "new_arrivals": new_arrivals,
        "personalized": personalized,
        "similar": similar,
    }
