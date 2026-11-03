"""Smoke estrutural do script sem instalar Streamlit (não substitui teste visual)."""
import runpy
import sys
import types
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ui_helpers import example

class State(dict):
    def __getattr__(self,key):
        try:return self[key]
        except KeyError as e:raise AttributeError(key) from e
    def __setattr__(self,key,value):self[key]=value

class UIObject:
    def __getattr__(self,name):return lambda *args,**kwargs:None
    def __enter__(self):return self
    def __exit__(self,*args):return False

class StStub(types.ModuleType):
    def __init__(self,nav='Visão geral',actions=None):
        super().__init__('streamlit')
        self.nav=nav;self.actions=set(actions or []);self.session_state=State()
        self.sidebar=UIObject();self.called=[]
        for module_name in ('ui_v04','ui_assistant','ui_document_ai'):
            if module_name in sys.modules:sys.modules[module_name].st=self
    def __getattr__(self,name):
        if name in {'form','expander','spinner','container'}:return lambda *a,**kw:UIObject()
        if name=='columns':return lambda count,*a,**kw:[UIObject() for _ in range(count if isinstance(count,int) else len(count))]
        if name=='tabs':return lambda labels,*a,**kw:[UIObject() for _ in labels]
        if name=='radio':return lambda label,opts,*a,**kw:self.nav if label=='Navegação' else list(opts)[kw.get('index',0)]
        if name=='selectbox':
            return lambda label,opts,*a,**kw:list(opts)[kw.get('index',0)]
        if name=='multiselect':return lambda *a,**kw:kw.get('default',[]) or []
        if name in {'text_input','text_area'}:return lambda *a,**kw:kw.get('value','')
        if name in {'button','form_submit_button'}:
            def click(label,*a,**kw):
                return (not kw.get('disabled',False)) and (kw.get('key') or label) in self.actions
            return click
        if name=='file_uploader':return lambda *a,**kw:None
        if name=='rerun':return lambda *a,**kw:None
        if name=='set_page_config':return lambda *a,**kw:None
        def no_op(*a,**kw):
            self.called.append(name)
            return None
        return no_op

class TestSmoke(unittest.TestCase):
    def test_all_screens_render_without_python_errors(self):
        for nav in ['Início','Avaliação','Comparação','Projetos','Avançado','Visão geral','Produto','Componentes','Dados técnicos','Evidências','IA · Documentos','Assistente de ecodesign']:
            with self.subTest(nav=nav):
                st=StStub(nav)
                old=sys.modules.get('streamlit')
                sys.modules['streamlit']=st
                try:runpy.run_path(str(ROOT/'app.py'))
                finally:
                    if old is None:sys.modules.pop('streamlit',None)
                    else:sys.modules['streamlit']=old
                self.assertIn('case',st.session_state)

    def test_json_import_requires_confirmation_in_projects(self):
        """Importar JSON por Projetos exige prévia e confirmação explícita."""
        from types import SimpleNamespace
        fixture = (ROOT/'examples'/'teste_rotulo_pvc_input.json').read_bytes()
        st = StStub('Projetos', actions={'v04_confirm_project_import'})
        st.file_uploader = lambda *a,**kw: SimpleNamespace(getvalue=lambda: fixture)
        old = sys.modules.get('streamlit');sys.modules['streamlit'] = st
        try:runpy.run_path(str(ROOT/'app.py'))
        finally:
            if old is None: sys.modules.pop('streamlit',None)
            else: sys.modules['streamlit']=old
        self.assertEqual(st.session_state.case['product_id'],'novo-produto')

        st = StStub('Projetos', actions={'v04_confirm_project_import'})
        st.file_uploader = lambda *a,**kw: SimpleNamespace(getvalue=lambda: fixture)
        st.checkbox = lambda label,*a,**kw: kw.get('key') == 'v04_import_confirm'
        old = sys.modules.get('streamlit');sys.modules['streamlit'] = st
        try:runpy.run_path(str(ROOT/'app.py'))
        finally:
            if old is None: sys.modules.pop('streamlit',None)
            else: sys.modules['streamlit']=old
        self.assertEqual(st.session_state.case['product_id'],'SYN-PET-PVC-LABEL-001')
        self.assertEqual(len(st.session_state.case['facts']),6)

    def test_evaluation_action_calls_original_motor(self):
        st=StStub('Avaliação',actions={'run_assessment'})
        st.session_state.guide_step_v04=3
        st.session_state.case=example()
        old=sys.modules.get('streamlit');sys.modules['streamlit']=st
        try:runpy.run_path(str(ROOT/'app.py'))
        finally:
            if old is None:sys.modules.pop('streamlit',None)
            else:sys.modules['streamlit']=old
        report=st.session_state.assessment
        self.assertEqual(len(report['results']),15)
        self.assertEqual(report['global_recyclability_class'],'NAO_EMITIDA')
        self.assertEqual(report['scope'],'DENTRO')

if __name__=='__main__':unittest.main()
