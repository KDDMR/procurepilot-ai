@description('Azure region for the deployment.')
param location string = resourceGroup().location

@description('Short environment name used in resource names.')
@minLength(2)
@maxLength(12)
param environmentName string

@description('Container image produced by the delivery pipeline.')
param containerImage string

@description('Existing Azure OpenAI or Microsoft Foundry model endpoint.')
param azureOpenAiEndpoint string = ''

@description('Existing model deployment name.')
param azureOpenAiDeployment string = 'gpt-4.1-mini'

@secure()
@description('Demo credential. Prefer managed identity and Key Vault in production.')
param azureOpenAiApiKey string = ''

var suffix = uniqueString(resourceGroup().id, environmentName)
var tags = {
  application: 'procurepilot-ai'
  environment: environmentName
  managedBy: 'bicep'
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-procurepilot-${environmentName}-${suffix}'
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-procurepilot-${environmentName}-${suffix}'
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-procurepilot-${environmentName}-${suffix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-procurepilot-${environmentName}-${suffix}'
  location: location
  tags: union(tags, {
    'azd-service-name': 'api'
  })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      secrets: empty(azureOpenAiApiKey) ? [] : [
        {
          name: 'azure-openai-api-key'
          value: azureOpenAiApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
            {
              name: 'AI_PROVIDER'
              value: empty(azureOpenAiEndpoint) ? 'mock' : 'azure'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: azureOpenAiDeployment
            }
            {
              name: 'DATABASE_PATH'
              value: '/tmp/procurepilot.db'
            }
            {
              name: 'POLICY_DIRECTORY'
              value: '/app/policies'
            }
          ], empty(azureOpenAiApiKey) ? [] : [
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-api-key'
            }
          ])
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output applicationUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output applicationInsightsConnectionString string = insights.properties.ConnectionString

