from fastapi import FastAPI

from verifact_intake import __version__

app = FastAPI(
    title="VeriFact Intake",
    version=__version__,
    description="Evidence-linked document-to-ontology intake with human review.",
)


@app.get("/healthz", tags=["operations"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}

