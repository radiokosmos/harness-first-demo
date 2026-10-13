Our nightly agent runs unattended. `bin/verify-run <run dir>` (ci/verify-run.mjs) must decide, from the run's artifacts only, whether the run actually did its job. Right now it always says RUN OK.
Write the checks. Done when `bin/test-verify-run` passes: RUN OK for ci/fixtures/runs/ok, RUN FAILED for ci/fixtures/runs/expired-token. Keep the change inside ci/verify-run.mjs.
