import argparse
import json
from pathlib import Path
from .engine import assess


def main():
    parser=argparse.ArgumentParser(description='Motor de regras PET Circular v0.1 — sem certificação global')
    parser.add_argument('input',type=Path,help='Arquivo de entrada JSON conforme input.schema.json')
    parser.add_argument('-o','--output',type=Path,help='Saída JSON; sem opção, imprime no terminal')
    args=parser.parse_args()
    product=json.loads(args.input.read_text(encoding='utf-8'))
    result=assess(product)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+'\n',encoding='utf-8')
        print('Resultado salvo em',args.output)
    else:print(text)

if __name__=='__main__':main()
