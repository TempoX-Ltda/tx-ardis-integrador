
from tx import parse_args

def test_gerar_id_projeto():

    id_projeto = parse_args([
                "--host", "http://172.16.1.16:6543/",
                "-u", "admin",
                "-p", "qwe123",
                "--verbose",
                "plano_de_corte",
                "gerar_id_projeto",
                "--dst-file", "project_id"
            ])
    
    print(id_projeto)