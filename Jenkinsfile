// CI for this repo. Every stage runs a script that also runs somewhere else (the GitHub Actions
// workflow, or by hand); nothing is re-implemented here, so the gates cannot drift apart.
pipeline {
  agent { label 'linux' }
  options { timestamps(); disableConcurrentBuilds() }
  environment {
    PATH = "${HOME}/.local/bin:${PATH}"
    // Pinned installer: an unversioned one changes what the pipeline does without anyone deciding it.
    UV_PIN = '0.4.29'
  }
  stages {
    stage('checkout') {
      steps {
        checkout scm
        // A pull-request checkout only fetches its own head: fetch the target explicitly, because
        // two stages below judge "what this PR adds" against it. The `sh` step does NOT inherit the
        // checkout's credential (measured: "could not read Username", rc=128, on a private repo), so
        // git gets it through GIT_ASKPASS: never in the URL, argv or the trace.
        withCredentials([gitUsernamePassword(credentialsId: 'scm-api-token')]) {
          sh '''
            if [ -n "${CHANGE_TARGET:-}" ]; then
              git fetch --quiet origin "+refs/heads/${CHANGE_TARGET}:refs/remotes/origin/${CHANGE_TARGET}"
              # A base equal to this commit means an empty range: every gate below would pass
              # without reading anything.
              if [ "$(git rev-parse "origin/${CHANGE_TARGET}")" = "$(git rev-parse HEAD)" ]; then
                echo "the pull request base is this very commit: nothing to judge. Failing closed." >&2
                exit 1
              fi
            fi
          '''
        }
      }
    }

    stage('uv') {
      steps {
        sh 'command -v uv >/dev/null 2>&1 || curl -LsSf "https://astral.sh/uv/${UV_PIN}/install.sh" | sh'
      }
    }

    stage('repo policy') {
      steps { sh 'python3 tools/repo_policy_check.py' }
    }

    stage('language: tree') {
      steps { sh 'bash tools/lang_gate.sh tree' }
    }

    stage('language: commit messages') {
      steps {
        sh '''
          if [ -n "${CHANGE_TARGET:-}" ]; then
            bash tools/lang_commits.sh "origin/${CHANGE_TARGET}" HEAD
          else
            bash tools/lang_commits.sh HEAD~1 HEAD   # branch build: the commit that was just pushed
          fi
        '''
      }
    }

    stage('language: PR title and description') {
      when { changeRequest() }
      steps {
        withCredentials([usernamePassword(credentialsId: 'scm-api-token',
                                          usernameVariable: 'API_USER', passwordVariable: 'API_TOKEN')]) {
          // Never print API_USER or API_TOKEN: for this credential class the token also comes out
          // as the user name.
          sh '''
            set -eu
            { set +x; } 2>/dev/null   # keep the token out of the build trace
            export PR_TEXT_FILE="$(mktemp)"
            trap 'rm -f "$PR_TEXT_FILE"' EXIT
            python3 tools/pr_text.py
            bash tools/lang_gate.sh pr-text "$PR_TEXT_FILE"
          '''
        }
      }
    }

    stage('secret scan') {
      steps {
        // The scanner lives in a private repository, so its address is a global Jenkins variable
        // (a raw URL pinned by commit), not something written in this public file. No variable,
        // no scan: fail closed, because a skipped scan is indistinguishable from a clean one.
        withCredentials([usernamePassword(credentialsId: 'scm-api-token',
                                          usernameVariable: 'API_USER', passwordVariable: 'API_TOKEN')]) {
          sh '''
          set -eu
          : "${SECRET_SCAN_URL:?SECRET_SCAN_URL is not set on the CI server. Failing closed.}"
          { set +x; } 2>/dev/null
          printf 'header = "Authorization: token %s"\\n' "${API_TOKEN}" | curl -fsSL --config - \
            "${SECRET_SCAN_URL}" -o "${WORKSPACE_TMP}/secret-scan"
          set -x
          # Only what the branch adds is judged. A base that IS this commit gives an empty
          # diff, which reads as clean without looking, so such a base is discarded; and the
          # previous SUCCESSFUL build is used, never the previous build: a red build must
          # not use up the finding. No usable base: fail closed.
          head="$(git rev-parse HEAD)"
          base=""
          for candidate in ${CHANGE_TARGET:+"origin/${CHANGE_TARGET}"} "${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-}" "HEAD~1"; do
            [ -n "$candidate" ] || continue
            sha="$(git rev-parse --verify --quiet "${candidate}^{commit}")" || continue
            [ "$sha" != "$head" ] || continue
            git merge-base --is-ancestor "$sha" "$head" || [ -n "${CHANGE_TARGET:-}" ] || continue
            base="$sha"
            break
          done
          [ -n "$base" ] || { echo "secret-scan: no base other than this very commit. Failing closed." >&2; exit 1; }
          python3 "${WORKSPACE_TMP}/secret-scan" --against "$base"
        '''
        }
      }
    }
  }
}
