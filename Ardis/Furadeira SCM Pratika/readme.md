Pegar o último arquivo, pode ser pelo nome jaque o nome é a data, ou pela data de modificaçao

ignorar primeira linha que é o cabecalho

para cada linha que for processada, adicionar a linha, no arquivo <nome do csv>_PROCESSADO_TEMPOX.csv

se a linha já existir, nao apontar
se a linha nao existir, fazer apontamento

enviar info para endpoint /leitura, ver campos obrigatorios

01,45,47,00048
IJ,Z:\PRATIKAS\@ USINAGENS\NESTING ( PLANEJADOS )\2025\ABRIL\Plano_812\FRE00007278A.PGM,,851,199,18.5,08,57,51,08,59,47,00,01,56,00,01,56,1,00,01,56,00


nesse caso, precisa ser enviado para a APi o valor FRE00007278A, pra isso pode intepretar esse segundo campo com o PathLib do Python, e extrair o nome do arquivo

>>> from pathlib import Path
>>> caminho = Path("Z:\PRATIKAS\@ USINAGENS\NESTING ( PLANEJADOS )\2025\ABRIL\Plano_812\FRE00007278A.PGM")
  File "<stdin>", line 1
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 23-24: malformed \N character escape
>>> caminho = Path(r"Z:\PRATIKAS\@ USINAGENS\NESTING ( PLANEJADOS )\2025\ABRIL\Plano_812\FRE00007278A.PGM")
>>> caminho
PosixPath('Z:\\PRATIKAS\\@ USINAGENS\\NESTING ( PLANEJADOS )\\2025\\ABRIL\\Plano_812\\FRE00007278A.PGM')
>>> caminho.name
'Z:\\PRATIKAS\\@ USINAGENS\\NESTING ( PLANEJADOS )\\2025\\ABRIL\\Plano_812\\FRE00007278A.PGM'
>>> caminho.
caminho.absolute(         caminho.group(            caminho.is_socket(        caminho.open(             caminho.resolve(          caminho.touch(
caminho.anchor            caminho.home(             caminho.is_symlink(       caminho.owner(            caminho.rglob(            caminho.unlink(
caminho.as_posix(         caminho.is_absolute(      caminho.iterdir(          caminho.parent            caminho.rmdir(            caminho.with_name(
caminho.as_uri(           caminho.is_block_device(  caminho.joinpath(         caminho.parents           caminho.root              caminho.with_suffix(
caminho.chmod(            caminho.is_char_device(   caminho.lchmod(           caminho.parts             caminho.samefile(         caminho.write_bytes(
caminho.cwd(              caminho.is_dir(           caminho.link_to(          caminho.read_bytes(       caminho.stat(             caminho.write_text(
caminho.drive             caminho.is_fifo(          caminho.lstat(            caminho.read_text(        caminho.stem              
caminho.exists(           caminho.is_file(          caminho.match(            caminho.relative_to(      caminho.suffix            
caminho.expanduser(       caminho.is_mount(         caminho.mkdir(            caminho.rename(           caminho.suffixes          
caminho.glob(             caminho.is_reserved(      caminho.name              caminho.replace(          caminho.symlink_to(       
>>> caminho.exists()
False
>>> caminho.is_file()
False
>>> caminho.suffix
'.PGM'
>>> caminho.stem
'FRE00007278A'
>>> caminho
PosixPath('Z:/PRATIKAS/@ USINAGENS/NESTING ( PLANEJADOS )/2025/ABRIL/Plano_812/FRE00007278A.PGM')
>>> caminho.suffix
'.PGM'
>>> caminho.stem
'FRE00007278A'