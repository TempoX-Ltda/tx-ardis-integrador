Pegar o último arquivo, pode ser pelo nome jaque o nome é a data, ou pela data de modificaçao

ignorar primeira linha que é o cabecalho

para cada linha que for processada, adicionar a linha, no arquivo <nome do csv>_PROCESSADO_TEMPOX.csv

se a linha já existir, nao apontar
se a linha nao existir, fazer apontamento

enviar info para endpoint /leitura, ver campos obrigatorios

Username,PanelID,Date,Start,End,FeedPanelEnd,FeedTime,Duration,Size,ProcessSide,Area,HoleCount,GrooveCount,MillCount,WorkArea,PositioningEnd,PositioningTime
,GAV00043639A,2025/05/01,00:00:46,00:01:07,00:00:48,1.560,18.782,688 x 275.5 x 15.3,XY1,.190,6,0,0,Default,00:00:47,.702

enviar campo PanelID