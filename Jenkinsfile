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
    stage('checkout') { steps { checkout scm } }

    stage('uv') {
      steps {
        sh 'command -v uv >/dev/null 2>&1 || curl -LsSf "https://astral.sh/uv/${UV_PIN}/install.sh" | sh'
      }
    }

    stage('repo policy') {
      steps { sh 'python3 tools/gates/check-repo-policy.py' }
    }

    stage('language: tree') {
      steps { sh 'bash tools/gates/lang-gate.sh tree' }
    }

    stage('language: commit messages') {
      steps {
        sh '''
          set -eu
          if [ -n "${CHANGE_TARGET:-}" ]; then
            # A pull-request checkout only fetches its own head: fetch the target explicitly.
            git fetch --quiet origin "+refs/heads/${CHANGE_TARGET}:refs/remotes/origin/${CHANGE_TARGET}"
            RANGE="origin/${CHANGE_TARGET}..HEAD"
          else
            RANGE="HEAD~1..HEAD"   # branch build: the commit that was just pushed
          fi
          bash tools/gates/lang-gate.sh commits "$RANGE"
        '''
      }
    }

    stage('language: PR title and description') {
      when { changeRequest() }
      steps {
        withCredentials([usernamePassword(credentialsId: 'scm-api-token',
                                          usernameVariable: 'API_USER', passwordVariable: 'API_TOKEN')]) {
          sh '''
            set -eu
            { set +x; } 2>/dev/null   # keep the token out of the build trace
            PR_BODY="$(python3 tools/gates/fetch-pr-body.py)"
            export PR_BODY PR_TITLE="${CHANGE_TITLE}"
            bash tools/gates/lang-gate.sh pr-text
          '''
        }
      }
    }
  }
}
