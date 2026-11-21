# Kullanım: proje kök klasöründe  python fuzz_oracle.py
# Rastgele soru üretir, cevabı araçtan bağımsız (sympy + sayısal) kontrol eder.
import sys, warnings, random, signal; warnings.filterwarnings("ignore"); sys.path.insert(0,".")
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
TR=standard_transformations+(implicit_multiplication_application,convert_xor)
def P(t): return parse_expr(t.replace('e^(','exp(').replace('e^x','exp(x)'),transformations=TR,local_dict={'x':sp.Symbol('x')})
from mathpad import MathPad
e=MathPad(); x=sp.Symbol("x"); random.seed(7)
fails={}
def rec(cat,q,why):
    fails.setdefault(cat,[]).append((q,why))
class TO(Exception): pass
def h(s,f): raise TO()
signal.signal(signal.SIGALRM,h)
def ask(q):
    signal.alarm(10)
    try: return e.ask(q)
    finally: signal.alarm(0)
def ps(t): return sp.sympify(t.replace("^","**"),locals={"x":x})
def num_ok(a,b,tol=1e-6):
    try: return abs(complex(sp.N(a))-complex(sp.N(b)))<tol
    except Exception: return False
N=40
# 1 quadratics
for _ in range(N):
    a,b,c=random.randint(1,5),random.randint(-9,9),random.randint(-9,9)
    q=f"{a}x^2{b:+d}x{c:+d}=0".replace("+-","-")
    try:
        s=ask(q); roots=sp.solve(a*x**2+b*x+c,x)
        got=[v for d in s.result for v in d.values()] if isinstance(s.result,list) else None
        if got is None or len(set(sp.nsimplify(g) for g in got))!=len(set(roots)) or not all(any(num_ok(g,r) for r in roots) for g in got): rec("quad",q,f"{s.result_text} vs {roots}")
    except Exception as ex: rec("quad",q,repr(ex)[:80])
# 2 derivatives
fs=["x^3*sin(x)","ln(x^2+{k})","e^({k}x)*cos(x)","(x^2+{k})/(x-{j})","sqrt(x^2+{k})","x^{k}*ln(x)","sin({k}x)^2","tan({k}x)","(x+{k})^{j}"]
for _ in range(N):
    k,j=random.randint(2,5),random.randint(2,6); f=random.choice(fs).format(k=k,j=j)
    q=f"d/dx {f}"
    try:
        s=ask(q); fe=P(f)
        exp=sp.diff(fe,x)
        if not all(num_ok(s.result.subs(x,v),exp.subs(x,v)) for v in (1.3,2.1)): rec("deriv",q,f"{s.result_text} vs {exp}")
    except Exception as ex: rec("deriv",q,repr(ex)[:80])
# 3 definite integrals
ints=["{k}x^2-{j}x+1","(x+{k})^3","e^({k}x)","sin({k}x)","cos({j}x)","1/({k}x+1)","x*e^x","x^2*ln(x)","1/(x^2+{k})","sqrt({k}x+1)"]
for _ in range(N):
    k,j=random.randint(2,5),random.randint(2,6); f=random.choice(ints).format(k=k,j=j)
    lo,hi=(1,random.randint(2,4)) if "ln" in f else (0,random.randint(1,3))
    q=f"integral of {f} from {lo} to {hi}"
    try:
        s=ask(q); fe=P(f)
        exp=sp.Integral(fe,(x,lo,hi)).evalf(15)
        if not num_ok(s.result,exp): rec("integral",q,f"{s.result_text} vs {exp}")
    except Exception as ex: rec("integral",q,repr(ex)[:80])
# 4 systems
for _ in range(N):
    a,b,c,d_=[random.randint(-5,5) for _ in range(4)]
    if a*d_-b*c==0: continue
    r1,r2=random.randint(-9,9),random.randint(-9,9)
    q=f"{a}x{b:+d}y={a*r1+b*r2}, {c}x{d_:+d}y={c*r1+d_*r2}"
    try:
        s=ask(q); sol=s.result[0]
        if not (num_ok(sol[sp.Symbol('x')],r1) and num_ok(sol[sp.Symbol('y')],r2)): rec("system",q,f"{s.result_text} vs ({r1},{r2})")
    except Exception as ex: rec("system",q,repr(ex)[:80])
# 5 limits
lims=[("(x^2-{k})/(x-{s})",None),("sin({k}x)/x",None),("(e^({k}x)-1)/x",None),("tan({k}x)/x",None),("(1-cos(x))/x^2",None)]
for _ in range(20):
    k=random.randint(2,5); f,_=random.choice(lims)
    if "{s}" in f: s_=k; f2=f.format(k=s_*s_,s=s_); pt=s_
    else: f2=f.format(k=k); pt=0
    q=f"limit x->{pt} {f2}"
    try:
        s=ask(q); fe=P(f2); exp=sp.limit(fe,x,pt)
        if not num_ok(s.result,exp): rec("limit",q,f"{s.result_text} vs {exp}")
    except Exception as ex: rec("limit",q,repr(ex)[:80])
# 6 areas
for _ in range(25):
    k=random.randint(1,4); m=random.randint(1,3)
    pool=[(f"y=x^2, y={k*k}", sp.Rational(4,3)*k**3),(f"y=x^2, y={k}x", sp.Rational(k**3,6)),(f"y=x^3, y=0, x=0, x={m+1}", sp.Rational((m+1)**4,4)),(f"y=x^2+{k}, y=0, x=0, x={m}", sp.Rational(m**3,3)+k*m),(f"y=sqrt(x), y=0, x={m*m}", sp.Rational(2,3)*m**3)]
    q,exp=random.choice(pool); q+=" meýdany"
    try:
        s=ask(q)
        if not num_ok(s.result,exp): rec("area",q,f"{s.result_text} vs {exp}")
    except Exception as ex: rec("area",q,repr(ex)[:80])
tot=sum(len(v) for v in fails.values()); print("TOPLAM HATA:",tot)
for c,l in fails.items():
    print(f"--{c}: {len(l)}")
    for q,w in l[:5]: print("   ",q,"->",w[:110])
