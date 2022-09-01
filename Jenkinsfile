@Library(['aic-jenkins-sharedlib']) _

pythonBuildPipeline {
    habilitarValidacaoEstatica      = true // habilita a validação estática do código fonte
    habilitarValidacaoSeguranca     = false // habilita a validação de segurança do código fonte
    habilitarConstrucao             = true // habilita a construção da aplicação
    habilitarTestesUnidade          = false // habilita a execução dos testes de unidade
    habilitarTestesIntegracao       = false // habilita a execução dos testes de integração
    habilitarSonar                  = false // habilita a execução do SonarQube Scanner
    habilitarEmpacotamento          = true // habilita o empacotamento da aplicação
    habilitarEmpacotamentoDocker    = true // habilita o build e publicação da imagem docker
    habilitarPublicacao             = true // habilita a publicação do pacote no repositório corporativo
    habilitarDebug                  = false // habilita debug
}
// Documentação das pipelines: https://fontes.intranet.bb.com.br/aic/publico/atendimento/-/wikis/Pipelines