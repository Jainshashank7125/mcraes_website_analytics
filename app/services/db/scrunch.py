from typing import List, Dict, Optional, Any
from sqlalchemy import and_, or_
from app.db.models import Brand, Prompt, Response, Citation
from app.services.db.base import BaseDB
import logging

logger = logging.getLogger(__name__)


class ScrunchDBMixin(BaseDB):
    """Scrunch AI database methods"""

    def upsert_brands(self, brands: List[Dict]) -> int:
        """Upsert brands data - Optimized with bulk operations"""
        if not brands:
            return 0

        try:
            # Extract all brand IDs for bulk lookup
            brand_ids = [b.get("id") for b in brands if b.get("id")]
            if not brand_ids:
                return 0

            # Bulk fetch existing brands in one query
            existing_brands = {
                b.id: b for b in self.db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
            }

            # Separate into updates and inserts
            to_update = []
            to_insert = []

            for brand_data in brands:
                brand_id = brand_data.get("id")
                if not brand_id:
                    continue

                if brand_id in existing_brands:
                    # Update existing
                    existing = existing_brands[brand_id]
                    existing.name = brand_data.get("name")
                    existing.website = brand_data.get("website")
                    if "ga4_property_id" in brand_data:
                        existing.ga4_property_id = brand_data.get("ga4_property_id")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Brand(
                        id=brand_id,
                        name=brand_data.get("name"),
                        website=brand_data.get("website"),
                        ga4_property_id=brand_data.get("ga4_property_id")
                    ))

            # Bulk add new brands
            if to_insert:
                self.db.bulk_save_objects(to_insert)

            # Commit once for all changes
            self.db.commit()

            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} brands ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting brands: {str(e)}")
            raise

    def upsert_prompts(self, prompts: List[Dict], brand_id: int = None) -> int:
        """Upsert prompts data - Optimized with bulk operations"""
        if not prompts:
            return 0

        try:
            # Extract all prompt IDs for bulk lookup
            prompt_ids = [p.get("id") for p in prompts if p.get("id")]
            if not prompt_ids:
                return 0

            # Bulk fetch existing prompts in one query
            existing_prompts = {
                p.id: p for p in self.db.query(Prompt).filter(Prompt.id.in_(prompt_ids)).all()
            }

            # Separate into updates and inserts
            to_update = []
            to_insert = []

            for prompt_data in prompts:
                prompt_id = prompt_data.get("id")
                if not prompt_id:
                    continue

                final_brand_id = brand_id or prompt_data.get("brand_id")

                if prompt_id in existing_prompts:
                    # Update existing
                    existing = existing_prompts[prompt_id]
                    existing.brand_id = final_brand_id
                    existing.text = prompt_data.get("text")
                    existing.stage = prompt_data.get("stage")
                    existing.persona_id = prompt_data.get("persona_id")
                    existing.persona_name = prompt_data.get("persona_name")
                    existing.platforms = prompt_data.get("platforms", [])
                    existing.tags = prompt_data.get("tags", [])
                    existing.topics = prompt_data.get("topics", [])
                    if prompt_data.get("created_at"):
                        existing.created_at = prompt_data.get("created_at")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Prompt(
                        id=prompt_id,
                        brand_id=final_brand_id,
                        text=prompt_data.get("text"),
                        stage=prompt_data.get("stage"),
                        persona_id=prompt_data.get("persona_id"),
                        persona_name=prompt_data.get("persona_name"),
                        platforms=prompt_data.get("platforms", []),
                        tags=prompt_data.get("tags", []),
                        topics=prompt_data.get("topics", []),
                        created_at=prompt_data.get("created_at")
                    ))

            # Bulk add new prompts
            if to_insert:
                self.db.bulk_save_objects(to_insert)

            # Commit once for all changes
            self.db.commit()

            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} prompts ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting prompts: {str(e)}")
            raise

    def upsert_responses(self, responses: List[Dict], brand_id: int = None) -> int:
        """Upsert responses data - Optimized with bulk operations"""
        if not responses:
            return 0

        try:
            batch_size = 500  # Increased batch size for better performance
            total_upserted = 0

            for i in range(0, len(responses), batch_size):
                batch = responses[i:i + batch_size]

                # Extract all response IDs for bulk lookup
                response_ids = [r.get("id") for r in batch if r.get("id")]
                if not response_ids:
                    continue

                # Bulk fetch existing responses in one query
                existing_responses = {
                    r.id: r for r in self.db.query(Response).filter(Response.id.in_(response_ids)).all()
                }

                # Separate into updates and inserts
                to_update = []
                to_insert = []

                for response_data in batch:
                    response_id = response_data.get("id")
                    if not response_id:
                        continue

                    final_brand_id = brand_id or response_data.get("brand_id")

                    # Extract data
                    citations = response_data.get("citations", [])
                    competitors_present = response_data.get("competitors_present", [])
                    if not isinstance(competitors_present, list):
                        competitors_present = []
                    competitors = response_data.get("competitors", [])

                    if response_id in existing_responses:
                        # Update existing
                        existing = existing_responses[response_id]
                        existing.brand_id = final_brand_id
                        existing.prompt_id = response_data.get("prompt_id")
                        existing.prompt = response_data.get("prompt")
                        existing.response_text = response_data.get("response_text")
                        existing.platform = response_data.get("platform")
                        existing.country = response_data.get("country")
                        existing.persona_id = response_data.get("persona_id")
                        existing.persona_name = response_data.get("persona_name")
                        existing.stage = response_data.get("stage")
                        existing.branded = response_data.get("branded")
                        existing.tags = response_data.get("tags", [])
                        existing.key_topics = response_data.get("key_topics", [])
                        existing.brand_present = response_data.get("brand_present")
                        existing.brand_sentiment = response_data.get("brand_sentiment")
                        existing.brand_position = response_data.get("brand_position")
                        existing.competitors_present = competitors_present
                        existing.competitors = competitors
                        existing.citations = citations
                        if response_data.get("created_at"):
                            existing.created_at = response_data.get("created_at")
                        to_update.append(existing)
                    else:
                        # Insert new
                        to_insert.append(Response(
                            id=response_id,
                            brand_id=final_brand_id,
                            prompt_id=response_data.get("prompt_id"),
                            prompt=response_data.get("prompt"),
                            response_text=response_data.get("response_text"),
                            platform=response_data.get("platform"),
                            country=response_data.get("country"),
                            persona_id=response_data.get("persona_id"),
                            persona_name=response_data.get("persona_name"),
                            stage=response_data.get("stage"),
                            branded=response_data.get("branded"),
                            tags=response_data.get("tags", []),
                            key_topics=response_data.get("key_topics", []),
                            brand_present=response_data.get("brand_present"),
                            brand_sentiment=response_data.get("brand_sentiment"),
                            brand_position=response_data.get("brand_position"),
                            competitors_present=competitors_present,
                            competitors=competitors,
                            citations=citations,
                            created_at=response_data.get("created_at")
                        ))

                # Bulk add new responses
                if to_insert:
                    self.db.bulk_save_objects(to_insert)

                # Commit batch once
                self.db.commit()
                total_upserted += len(batch)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} responses ({len(to_update)} updated, {len(to_insert)} inserted)")

            logger.info(f"Total upserted {total_upserted} responses")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting responses: {str(e)}")
            raise

    def upsert_citations(self, responses: List[Dict]) -> int:
        """Upsert citations separately - Optimized with bulk operations"""
        if not responses:
            return 0

        try:
            # Collect all citations with their response_ids
            all_citations = []
            for response_data in responses:
                response_id = response_data.get("id")
                if not response_id:
                    continue
                citations = response_data.get("citations", [])
                for citation_data in citations:
                    all_citations.append({
                        "response_id": response_id,
                        "url": citation_data.get("url"),
                        "domain": citation_data.get("domain"),
                        "source_type": citation_data.get("source_type"),
                        "title": citation_data.get("title"),
                        "snippet": citation_data.get("snippet")
                    })

            if not all_citations:
                return 0

            # Build lookup keys for bulk fetch
            citation_keys = [(c["response_id"], c["url"]) for c in all_citations if c.get("url")]

            # Bulk fetch existing citations
            existing_citations = {}
            if citation_keys:
                # Fetch in batches to avoid IN clause limits
                batch_size = 1000
                for i in range(0, len(citation_keys), batch_size):
                    batch_keys = citation_keys[i:i + batch_size]
                    # Build OR conditions for batch
                    conditions = []
                    for response_id, url in batch_keys:
                        conditions.append(
                            and_(Citation.response_id == response_id, Citation.url == url)
                        )
                    if conditions:
                        batch_existing = self.db.query(Citation).filter(or_(*conditions)).all()
                        for cit in batch_existing:
                            existing_citations[(cit.response_id, cit.url)] = cit

            # Separate into updates and inserts
            to_update = []
            to_insert = []

            for citation_data in all_citations:
                key = (citation_data["response_id"], citation_data["url"])
                if key in existing_citations:
                    # Update existing
                    existing = existing_citations[key]
                    existing.domain = citation_data.get("domain")
                    existing.source_type = citation_data.get("source_type")
                    existing.title = citation_data.get("title")
                    existing.snippet = citation_data.get("snippet")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Citation(
                        response_id=citation_data["response_id"],
                        url=citation_data["url"],
                        domain=citation_data.get("domain"),
                        source_type=citation_data.get("source_type"),
                        title=citation_data.get("title"),
                        snippet=citation_data.get("snippet")
                    ))

            # Bulk add new citations
            if to_insert:
                self.db.bulk_save_objects(to_insert)

            # Commit once for all changes
            self.db.commit()

            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} citations ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting citations: {str(e)}")
            raise
