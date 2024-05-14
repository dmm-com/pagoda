{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "airone.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "airone.labels" -}}
helm.sh/chart: {{ include "airone.chart" . }}
{{ include "airone.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "airone.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
  Get the secret name.
*/}}
{{- define "airone.secretName" -}}
{{- if .Values.airone.existingSecret }}
  {{- printf "%s" .Values.airone.existingSecret -}}
{{- else -}}
  airone-secret
{{- end -}}
{{- end -}}

{{/*
Shared environment block used across each component.
*/}}
{{- define "airone.env" -}}
- name: WSGI_WORKERS
  value: {{ .Values.gunicorn.workers | quote }}
- name: WSGI_TIMEOUT
  value: {{ .Values.gunicorn.timeout | quote }}
- name: CELERY_CONCURRENCY
  value: {{ .Values.celery.concurrency | quote }}
- name: AIRONE_TAG
  value: {{ .Values.image.tag | quote }}
{{- if or .Values.airone.secretKey .Values.airone.existingSecret }}
- name: AIRONE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: secretKey
{{- end }}
{{- if .Values.airone.debug }}
- name: AIRONE_DEBUG
  value: {{ default  .Values.airone.debug | quote }}
{{- end }}
{{- if .Values.airone.title }}
- name: AIRONE_TITLE
  value: {{ default  .Values.airone.title | quote }}
{{- end }}
{{- if .Values.airone.subtitle }}
- name: AIRONE_SUBTITLE
  value: {{ default  .Values.airone.subtitle | quote }}
{{- end }}
{{- if .Values.airone.noteDesc }}
- name: AIRONE_NOTE_DESC
  value: {{ default  .Values.airone.noteDesc | quote }}
{{- end }}
{{- if .Values.airone.noteLink }}
- name: AIRONE_NOTE_LINK
  value: {{ default  .Values.airone.noteLink | quote }}
{{- end }}
{{- if .Values.airone.ssoDesc }}
- name: AIRONE_SSO_DESC
  value: {{ default  .Values.airone.ssoDesc | quote }}
{{- end }}
{{- if .Values.airone.paswordResetDisabled }}
- name: AIRONE_PASSWORD_RESET_DISABLED
  value: {{ default  .Values.airone.paswordResetDisabled | quote }}
{{- end }}
{{- if .Values.airone.extensions }}
- name: AIRONE_EXTENSIONS
  value: {{ default  .Values.airone.extensions | quote }}
{{- end }}
{{- if .Values.airone.ldap.enabled }}
- name: AIRONE_LDAP_ENABLE
  value: {{ default  .Values.airone.ldap.enabled | quote }}
- name: AIRONE_LDAP_SERVER
  value: {{ default  .Values.airone.ldap.server | quote }}
- name: AIRONE_LDAP_FILTER
  value: {{ default  .Values.airone.ldap.filter | quote }}
{{- end }}
{{- if .Values.airone.sso.enabled }}
- name: AIRONE_SSO_ENABLE
  value: {{ default  .Values.airone.sso.enabled | quote }}
- name: AIRONE_SSO_URL
  value: {{ default  .Values.airone.sso.url | quote }}
{{- if or .Values.airone.sso.privateKey .Values.airone.existingSecret }}
- name: AIRONE_SSO_PRIVATE_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: ssoPrivateKey
{{- end }}
- name: AIRONE_SSO_PUBLIC_CERT
  value: {{ default  .Values.airone.sso.publicCert | quote }}
- name: AIRONE_SSO_DISPLAY_NAME
  value: {{ default  .Values.airone.sso.displayName | quote }}
- name: AIRONE_SSO_CONTACT_NAME
  value: {{ default  .Values.airone.sso.contactName | quote }}
- name: AIRONE_SSO_CONTACT_EMAIL
  value: {{ default  .Values.airone.sso.contactEmail | quote }}
- name: AIRONE_SSO_PROVIDER
  value: {{ default  .Values.airone.sso.provider | quote }}
{{- if or .Values.airone.sso.entityId .Values.airone.existingSecret }}
- name: AIRONE_SSO_ENTITY_ID
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: ssoEntityId
{{- end }}
- name: AIRONE_SSO_LOGIN_URL
  value: {{ default  .Values.airone.sso.loginUrl | quote }}
{{- if or .Values.airone.sso.x509Cert .Values.airone.existingSecret }}
- name: AIRONE_SSO_X509_CERT
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: ssoX509Cert
{{- end }}
- name: AIRONE_SSO_USER_ID
  value: {{ default  .Values.airone.sso.userId | quote }}
{{- end }}
{{- if .Values.airone.fileStorePath }}
- name: AIRONE_FILE_STORE_PATH
  value: {{ default  .Values.airone.fileStorePath | quote }}
{{- end }}
{{- if .Values.airone.storage.enabled }}
- name: AIRONE_STORAGE_ENABLE
  value: {{ default  .Values.airone.storage.enabled | quote }}
- name: AIRONE_STORAGE_BUCKET_NAME
  value: {{ default  .Values.airone.storage.bucket | quote }}
{{- if or .Values.airone.storage.accessKey .Values.airone.existingSecret }}
- name: AIRONE_STORAGE_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: storageAccessKey
{{- end }}
{{- if or .Values.airone.storage.secretAccessKey .Values.airone.existingSecret }}
- name: AIRONE_STORAGE_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: storageSecretAccessKey
{{- end }}
{{- end }}
{{- if .Values.airone.email.enabled }}
- name: AIRONE_EMAIL_ENABLE
  value: {{ default  .Values.airone.email.enabled | quote }}
- name: AIRONE_EMAIL_HOST
  value: {{ default  .Values.airone.email.host | quote }}
- name: AIRONE_EMAIL_PORT
  value: {{ default  .Values.airone.email.port | quote }}
- name: AIRONE_EMAIL_HOST_USER
  value: {{ default  .Values.airone.email.user | quote }}
{{- if or .Values.airone.email.password .Values.airone.existingSecret }}
- name: AIRONE_EMAIL_HOST_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: emailPassword
{{- end }}
- name: AIRONE_EMAIL_USE_TLS
  value: {{ default  .Values.airone.email.useTls | quote }}
- name: AIRONE_EMAIL_FROM
  value: {{ default  .Values.airone.email.from | quote }}
- name: AIRONE_EMAIL_ADMINS
  value: {{ default  .Values.airone.email.to | quote }}
{{- end }}
{{- if .Values.airone.datadog.enabled }}
- name: AIRONE_DATADOG_ENABLE
  value: {{ default  .Values.airone.datadog.enabled | quote }}
- name: AIRONE_DATADOG_TAG
  value: {{ default  .Values.airone.datadog.tag | quote }}
{{- end }}
{{- if not .Values.mysql.enabled }}
  {{- if .Values.externalMySQL }}
- name: AIRONE_MYSQL_USER
  value: {{ .Values.externalMySQL.user }}
    {{- if or .Values.externalMySQL.password .Values.airone.existingSecret }}
- name: AIRONE_MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: mysqlPassword
    {{- end }}
- name: AIRONE_MYSQL_MASTER_HOST
  value: {{ .Values.externalMySQL.master }}
- name: AIRONE_MYSQL_SLAVE_HOST
  value: {{ .Values.externalMySQL.slave }}
  {{- end }}
{{- else }}
- name: AIRONE_MYSQL_USER
  value: {{ .Values.mysql.credentials.root.user }}
- name: AIRONE_MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Release.Name }}-cluster-secret
      key: rootPassword
- name: AIRONE_MYSQL_MASTER_HOST
  value: {{ .Release.Name }}-instances:3306
- name: AIRONE_MYSQL_SLAVE_HOST
  value: {{ .Release.Name }}-instances:6447
{{- end }}
- name: AIRONE_MYSQL_DATABASE
  value: {{ .Values.airone.database }}
{{- if not .Values.elasticsearch.enabled }}
  {{- if .Values.externalElasticsearch }}
- name: AIRONE_ELASTICSEARCH_USER
  value: {{ .Values.externalElasticsearch.user }}
    {{- if or .Values.externalElasticsearch.password .Values.airone.existingSecret }}
- name: AIRONE_ELASTICSEARCH_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: elasticsearchPassword
    {{- end }}
- name: AIRONE_ELASTICSEARCH_HOST
  value: {{ .Values.externalElasticsearch.host }}
  {{- end }}
{{- else }}
- name: AIRONE_ELASTICSEARCH_USER
  value: elastic
{{/*
- name: AIRONE_ELASTICSEARCH_PASSWORD
  valueFrom:
    secretKeyRef:
      name: elasticsearch-master-credentials
      key: password
*/}}
- name: AIRONE_ELASTICSEARCH_PASSWORD
  value: password
- name: AIRONE_ELASTICSEARCH_HOST
  value: elasticsearch-master:9200
{{- end }}
- name: AIRONE_ELASTICSEARCH_INDEX
  value: {{ .Values.airone.index }}
{{- if not .Values.rabbitmq.enabled }}
  {{- if .Values.externalRabbitmq }}
- name: AIRONE_RABBITMQ_USER
  value: {{ .Values.externalRabbitmq.user }}
    {{- if or .Values.externalRabbitmq.password .Values.airone.existingSecret }}
- name: AIRONE_RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "airone.secretName" . }}
      key: rabbitmqPassword
    {{- end }}
- name: AIRONE_RABBITMQ_HOST
  value: {{ .Values.externalRabbitmq.host }}
  {{- end }}
{{- else }}
- name: AIRONE_RABBITMQ_USER
  value: {{ .Values.rabbitmq.auth.username }}
- name: AIRONE_RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Release.Name }}-rabbitmq
      key: rabbitmq-password
- name: AIRONE_RABBITMQ_HOST
  value: airone-rabbitmq
{{- end }}
{{- end -}}