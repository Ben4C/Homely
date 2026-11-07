"""Local operator import and bounded change-monitoring commands; no automatic publication."""

import argparse
import hashlib
import json
import os
from urllib.parse import urlparse
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine_for
from .models import Source, ImportDraft
from .schemas import CatalogInput
from .ingestion import import_catalog, stage_change


# Purpose: Import reviewed catalog data or flag changed official sources for review. Inputs: explicit CLI arguments; outputs: counts without secrets.
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    load = sub.add_parser("import")
    load.add_argument("file")
    load.add_argument("--publish-reviewed", action="store_true")
    load.add_argument("--reviewer", default="local-operator")
    leads = sub.add_parser("import-leads")
    leads.add_argument("file")
    sub.add_parser("check-sources")
    args = parser.parse_args()
    engine = engine_for(os.environ["DATABASE_URL"])
    with Session(engine) as session, session.begin():
        if args.command == "import":
            with open(args.file, encoding="utf-8-sig") as handle:
                catalog = CatalogInput.model_validate(json.load(handle))
            print(
                json.dumps(
                    import_catalog(
                        session, catalog, args.publish_reviewed, args.reviewer
                    )
                )
            )
        elif args.command == "import-leads":
            from pydantic import HttpUrl, TypeAdapter

            with open(args.file, encoding="utf-8-sig") as handle:
                records = json.load(handle)["leads"]
            for record in records:
                record["url"] = str(TypeAdapter(HttpUrl).validate_python(record["url"]))
                stage_change(
                    session,
                    "LEAD",
                    "lead-" + hashlib.sha256(record["url"].encode()).hexdigest()[:20],
                    record,
                )
            print(
                json.dumps({"manual_review_leads": len(records), "programs_created": 0})
            )
        else:
            checked = 0
            flagged = 0
            for source in session.scalars(select(Source)):
                parsed = urlparse(source.url)
                # Only previously curated official hosts; redirects are not followed and private IP URLs are forbidden.
                if (
                    parsed.scheme != "https"
                    or parsed.port not in {None, 443}
                    or parsed.hostname
                    not in {
                        "www.hcd.ca.gov",
                        "www.calhfa.ca.gov",
                        "www.anaheim.net",
                        "ggcity.org",
                        "cityofirvine.gov",
                        "www.cityoffullerton.com",
                        "habitatoc.org",
                        "www.habitatla.org",
                        "www.sandiegohabitat.org",
                    }
                ):
                    continue
                try:
                    with httpx.Client(timeout=15, follow_redirects=False) as client:
                        with client.stream("GET", source.url) as response:
                            response.raise_for_status()
                            data = b""
                            for chunk in response.iter_bytes():
                                data += chunk
                                if len(data) > 5 * 1024 * 1024:
                                    raise ValueError("Source exceeds retrieval limit")
                    digest = hashlib.sha256(data).hexdigest()
                    checked += 1
                    if source.content_hash is None or digest != source.content_hash:
                        stage_change(
                            session,
                            "SOURCE",
                            source.id,
                            {
                                "source_url": source.url,
                                "content_hash": digest,
                                "review_required": True,
                            },
                        )
                        flagged += 1
                except (httpx.HTTPError, ValueError):
                    stage_change(
                        session,
                        "SOURCE",
                        source.id,
                        {
                            "source_url": source.url,
                            "retrieval_failed": True,
                            "review_required": True,
                        },
                    )
                    flagged += 1
            print(
                json.dumps(
                    {"checked": checked, "flagged": flagged, "published_changes": 0}
                )
            )


if __name__ == "__main__":
    main()
