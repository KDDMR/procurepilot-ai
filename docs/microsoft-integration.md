# Microsoft integration path

## Azure OpenAI / Microsoft Foundry

The optional `AzureSemanticKernelProvider` connects the Narrative Agent to an Azure-hosted model
through Microsoft Semantic Kernel. Configure the endpoint, deployment and credential in `.env`.
All approval logic remains deterministic.

## Copilot Studio and Microsoft 365 Agents

FastAPI publishes an OpenAPI document at `/openapi.json`. A production deployment can expose selected
operations as a custom connector or agent action:

1. Deploy the API behind authenticated HTTPS.
2. Import `/openapi.json` into a custom connector.
3. Configure Microsoft Entra authentication.
4. Expose `POST /api/v1/assessments` as an assessment action.
5. Restrict the human decision action to authorised reviewer groups.
6. Use Power Automate or Teams adaptive cards for approval notifications.

The demo intentionally does not claim a live Microsoft 365 integration. This document describes the
concrete integration boundary and the additional identity controls required for production.

## Infrastructure

`infra/main.bicep` provisions an Azure Container Apps environment, Log Analytics, Application Insights
and a container app baseline. The model endpoint is supplied as configuration so an existing approved
Azure OpenAI or Foundry deployment can be reused.

