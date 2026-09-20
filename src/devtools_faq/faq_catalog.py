from dataclasses import dataclass


@dataclass(frozen=True)
class FaqEntry:
    slug: str
    question: str
    answer: str
    area: str

    @property
    def search_text(self) -> str:
        return f"{self.question}\n{self.answer}"


FAQ_ENTRIES = (
    FaqEntry(
        slug="build-cache-miss",
        question="Why did this build miss the dependency cache?",
        answer="Compare the lockfile digest and runtime version recorded by the build event.",
        area="build",
    ),
    FaqEntry(
        slug="build-exit-code",
        question="Where can I find the command that failed during a build?",
        answer="Open the failed build step and inspect its command, exit code, and diagnostic output.",
        area="build",
    ),
    FaqEntry(
        slug="release-rollback",
        question="How do I roll back a release?",
        answer="Promote the last healthy artifact and record the replaced release identifier.",
        area="release",
    ),
    FaqEntry(
        slug="release-pending",
        question="Why is my release still pending?",
        answer="Check the release operation for unfinished checks and the target environment status.",
        area="release",
    ),
    FaqEntry(
        slug="source-map-diagnostic",
        question="Why does a browser stack trace show bundled file names?",
        answer="Confirm that the release uploaded source maps for the same artifact identifier.",
        area="diagnostic",
    ),
    FaqEntry(
        slug="request-correlation",
        question="How do I trace one failed request across services?",
        answer="Search developer diagnostics with the request correlation identifier.",
        area="diagnostic",
    ),
)

