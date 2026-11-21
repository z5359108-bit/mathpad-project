# Kullanım: proje kök klasöründe  python fuzz_oracle2.py
# Eşitsizlik, mutlak değer, log, üstel, kök, ekstremum, teğet, dizi, integral, alan, limit, türev soruları üretip bağımsız doğrular.
import sys, warnings, random, signal; warnings.filterwarnings("ignore"); sys.path.insert(0,".")
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from mathpad import MathPad
e=MathPad(); x=sp.Symbol("x"); random.seed(2026)
TR=standard_transformations+(implicit_multiplication_application,convert_xor)
def P(t): return parse_expr(t.replace('e^(','exp(').replace('e^x','exp(x)'),transformations=TR,local_dict={'x':x})
class TO(Exception): pass
def h(s,f): raise TO()
signal.signal(signal.SIGALRM,h)
def ask(q):
    signal.alarm(12)
    try: return e.ask(q)
    finally: signal.alarm(0)
fails={}; counts={}
def run(cat,q,check):
    counts[cat]=counts.get(cat,0)+1
    try:
        s=ask(q); r=check(s)
        if r is not True: fails.setdefault(cat,[]).append((q,str(r)[:110]))
    except TO: fails.setdefault(cat,[]).append((q,"TIMEOUT"))
    except Exception as ex: fails.setdefault(cat,[]).append((q,"HATA "+repr(ex)[:90]))
def near(a,b,t=1e-6):
    try: return abs(complex(sp.N(a))-complex(sp.N(b)))<t
    except Exception: return False
def rootvals(res):
    out=[]
    for r in res:
        out.append(list(r.values())[0] if isinstance(r,dict) else r)
    return out
def sameroots(res,exp):
    g=sorted([complex(sp.N(v)) for v in rootvals(res)],key=lambda z:(z.real,z.imag))
    ex=sorted([complex(sp.N(v)) for v in exp],key=lambda z:(z.real,z.imag))
    return len(g)==len(ex) and all(abs(a-b)<1e-6 for a,b in zip(g,ex))
R=random.randint
# A quadratic inequalities
for _ in range(25):
    r1,r2=sorted(random.sample(range(-8,9),2)); a=R(1,3); op=random.choice(["<",">","<=",">="])
    poly=sp.expand(a*(x-r1)*(x-r2)); q=f"{str(poly).replace('**','^')}{op}0"
    def chk(s,poly=poly,op=op,r1=r1,r2=r2):
        res=s.result
        for t in [r1-3,r1,(r1+r2)/2+0.0 if r2>r1 else r1,r2,r2+3,(r1+r2)/2+0.37]:
            tv=poly.subs(x,sp.nsimplify(t)); exp={"<":tv<0,">":tv>0,"<=":tv<=0,">=":tv>=0}[op]
            if bool(res.contains(sp.nsimplify(t)))!=bool(exp): return f"t={t}: {res}"
        return True
    run("kvadrat_esitsizlik",q,chk)
# B abs equations / inequalities
for _ in range(25):
    a,b,c=R(1,4),R(-9,9),R(1,9); op=random.choice(["=","<",">","<=",">="])
    q=f"|{a}x{b:+d}|{op}{c}"
    def chk(s,a=a,b=b,c=c,op=op):
        if op=="=":
            return sameroots(s.result,[sp.Rational(c-b,a),sp.Rational(-c-b,a)]) or f"{s.result}"
        for t in [-10,-5,-2,-1,0,1,2,3,5,10,sp.Rational(c-b,a),sp.Rational(-c-b,a)]:
            v=abs(a*t+b); exp={"<":v<c,">":v>c,"<=":v<=c,">=":v>=c}[op]
            if bool(s.result.contains(sp.nsimplify(t)))!=bool(exp): return f"t={t}: {s.result}"
        return True
    run("mutlak_deger",q,chk)
# C log / exp
for _ in range(20):
    bs=R(2,5); k=R(1,4); d=R(1,3); c=R(1,5)
    q=f"log_{bs}(x+{c})={d}"; exp=[sp.Integer(bs)**d-c]
    run("log",q,lambda s,exp=exp: sameroots(s.result,exp) or str(s.result))
    q=f"{bs}^(x+{k})={bs**(k+d)}"; exp=[sp.Integer(d)]
    run("ustel",q,lambda s,exp=exp: sameroots(s.result,exp) or str(s.result))
# D radical
for _ in range(20):
    c=R(0,4); r=R(c+1,c+6) if c else R(1,6); # sqrt(x+b)=x-c with root r: r+b=(r-c)^2
    b=(r-c)**2-r; q=f"sqrt(x{b:+d})=x-{c}" if c else f"sqrt(x{b:+d})=x"
    ex=[sv for sv in sp.solve(sp.sqrt(x+b)-(x-c),x)]
    run("kok_denklem",q,lambda s,ex=ex: sameroots(s.result,ex) or str(s.result))
# E extrema cubic
for _ in range(20):
    p,qq=sorted(random.sample(range(-5,6),2))
    f=sp.expand(sp.integrate(3*(x-p)*(x-qq),x)); fs=str(f).replace("**","^")
    q=f"f(x)={fs} ekstremum"
    def chk(s,f=f,p=p,qq=qq):
        t=s.result if isinstance(s.result,str) else s.result_text
        t=t.replace("\\Rightarrow","").replace("\\quad"," ")
        vals=[sp.nsimplify(f.subs(x,v)) for v in (p,qq)]
        import re
        t=re.sub(r"\\frac\{(-?\d+)\}\{(\d+)\}",r"(\1/\2)",t); t=t.replace("- (","-(");t=re.sub(r"-\s+(\d)",r"-\1",t)
        nums=[float(sp.Rational(n)) if "/" in n else float(n) for n in re.findall(r"-?\(?-?\d+/\d+\)?|-?\d+(?:\.\d+)?",t.replace("(","").replace(")",""))]
        need=[p,qq]+[float(v) for v in vals]
        return all(any(abs(n-m)<1e-6 for n in nums) for m in need) or t
    run("ekstremum",q,chk)
# F tangent
for _ in range(20):
    a,b,c=R(1,3),R(-4,4),R(-5,5); x0=R(-3,3); f=a*x**2+b*x+c
    fs=str(sp.expand(f)).replace("**","^"); q=f"y={fs} eğrisine x0={x0} noktasında teğet"
    m=sp.diff(f,x).subs(x,x0); y0=f.subs(x,x0); line=m*(x-x0)+y0
    def chk(s,line=line):
        r=s.result; rhs=r.rhs if hasattr(r,"rhs") else sp.sympify(str(r).split("=")[-1])
        return sp.simplify(rhs-line)==0 or str(r)
    run("teget",q,chk)
# G sequences
for _ in range(20):
    a1,d,n=R(-5,9),R(-4,6),R(5,20); q=f"arifmetik progressiýa a1={a1} d={d} S_{n}"; ex=sp.Rational((2*a1+(n-1)*d)*n,2)
    run("arifm",q,lambda s,ex=ex: near(s.result,ex) or str(s.result))
    b1,qq,m=R(1,5),R(2,4),R(3,7); q=f"geometrik progressiýa b1={b1} q={qq} b{m}"; ex=b1*qq**(m-1)
    run("geom",q,lambda s,ex=ex: near(s.result,ex) or str(s.result))
# H indefinite integrals: derivative of result == integrand
ints=["x*e^x","x*cos({k}x)","x^2*sin(x)","ln(x)","x*ln(x)","1/(x+{k})","(x+{k})^{j}","e^({k}x)","sin({k}x)*cos({k}x)","x/(x^2+{k})","1/(x^2+{k}^2)"]
for _ in range(25):
    k,j=R(2,5),R(2,5); f=random.choice(ints).format(k=k,j=j)
    def chk(s,f=f):
        r=s.result
        if not isinstance(r,sp.Basic): return str(r)
        return all(near(sp.diff(r,x).subs(x,v),P(f).subs(x,v),1e-5) for v in (1.3,2.2,3.1)) or str(r)
    run("integral_belgisiz",f"integral of {f}",chk)
# I areas between parabola and line
for _ in range(20):
    a,b=sorted(random.sample(range(-4,5),2)); k=R(1,3)
    q=f"y=x^2, y={a+b}x-{a*b}".replace("--","+").replace("+-","-") # intersect at a,b
    ex=abs(sp.integrate((a+b)*x-a*b-x**2,(x,a,b)))
    if a==b: continue
    run("alan_parabola_dogru",q+" meýdany",lambda s,ex=ex: near(s.result,ex) or str(s.result))
# J limits at infinity and 0/0
for _ in range(20):
    a,b,c,d=R(1,5),R(-4,4),R(1,5),R(-4,4)
    q=f"limit x->oo ({a}x^2{b:+d}x+1)/({c}x^2{d:+d})"; ex=sp.Rational(a,c)
    run("limit_oo",q,lambda s,ex=ex: near(s.result,ex) or str(s.result))
    k=R(1,6); q=f"limit x->{k} (x^2-{k*k})/(x-{k})"
    run("limit_0_0",q,lambda s,k=k: near(s.result,2*k) or str(s.result))
# K second derivative and differential
for _ in range(20):
    a,b=R(1,5),R(2,5); f=f"{a}x^{b}+sin({b}x)"
    q=f"f(x)={f} ikinji önüm"; ex=sp.diff(P(f),x,2)
    run("ikinji_onum",q,lambda s,ex=ex: all(near(s.result.subs(x,v),ex.subs(x,v)) for v in (1.2,2.3)) or str(s.result))
    q=f"f(x)={f} diferensialyny tap"; ex=sp.diff(P(f),x)
    def chk(s,ex=ex):
        r=s.result; r=r.subs(sp.Symbol("dx"),1) if isinstance(r,sp.Basic) else r
        return all(near(r.subs(x,v),ex.subs(x,v)) for v in (1.2,2.3)) or str(s.result)
    run("diferensial",q,chk)
tot=sum(len(v) for v in fails.values()); print("SORU:",sum(counts.values()),"HATA:",tot)
for c in counts: print(f"{c}: {counts[c]-len(fails.get(c,[]))}/{counts[c]}")
for c,l in fails.items():
    print("--",c)
    for q,w in l[:4]: print("   ",q,"->",w)
