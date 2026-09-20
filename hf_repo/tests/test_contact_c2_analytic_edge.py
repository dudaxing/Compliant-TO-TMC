"""Independent moment identities and smooth-edge quadrature checks; no FE."""
from decimal import Decimal, localcontext
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from contact_c2_fields import comparison, gauss_legendre
from diagnose_contact_c2_analytic_edge import analytic_moments

D=Decimal


def gauss_moments(a,f0,f1,lam,mu,precision=120):
    with localcontext() as ctx:
        ctx.prec=precision
        A0,A1=D(0),D(0)
        for x,w in gauss_legendre(64,precision):
            t=(x+1)/2
            f=f0+(f1-f0)*t
            p=mu*f+(lam*(a*f).ln()-mu)/f
            A0+=w*p/2
            A1+=w*t*p/2
        return [A0,A1]


def test_constant_integral_and_half_moment():
    with localcontext() as ctx:
        ctx.prec=120
        a,f,lam,mu=map(D,("1.2",".8","2","3"))
        result=analytic_moments(a,f,f,lam,mu,precision=120)
        expected=mu*f+(lam*(a*f).ln()-mu)/f
        assert result["method"]=="constant"
        assert result["A0"]==expected and result["A1"]==expected/2


@pytest.mark.parametrize("f1,method",[(".9","harmonic_series"),(".6","harmonic_series"),("1.2","closed_form")])
def test_smooth_series_and_closed_form_agree_with_gauss64(f1,method):
    a,f0,lam,mu=map(D,("1.2",".8","2","3"))
    result=analytic_moments(a,f0,D(f1),lam,mu,precision=120)
    assert result["method"]==method
    quadrature=gauss_moments(a,f0,D(f1),lam,mu)
    check=comparison([result["A0"],result["A1"]],quadrature,unit="N/mm^2",limit="1e-95")
    assert check["status"]=="pass"


def test_small_slope_does_not_lose_first_order_increment():
    with localcontext() as ctx:
        ctx.prec=120
        a,f0,b,lam,mu=map(D,("1.2",".8","1e-50","2","3"))
        result=analytic_moments(a,f0,f0+b,lam,mu,precision=120)
        constant=analytic_moments(a,f0,f0,lam,mu,precision=120)
        derivative=mu+(lam-lam*(a*f0).ln()+mu)/(f0*f0)
        assert result["method"]=="harmonic_series" and result["terms"]>=2
        assert result["A0"]!=constant["A0"]
        assert abs(result["A0"]-constant["A0"]-b*derivative/2)<D("1e-98")
        assert abs(result["A1"]-constant["A1"]-b*derivative/3)<D("1e-98")
        low=analytic_moments(a,f0,f0+b,lam,mu,precision=80)
        assert comparison([low["A0"],low["A1"]],[result["A0"],result["A1"]],unit="N/mm^2")["status"]=="pass"


@pytest.mark.parametrize("f0,f1",[(".8",".9"),(".8","1.2"),(".7",".000015")])
def test_endpoint_reversal_and_cross_precision(f0,f1):
    a,lam,mu=map(D,("1.2",".0000576923076923",".0000384615384615"))
    with localcontext() as ctx:
        ctx.prec=120
        high=analytic_moments(a,D(f0),D(f1),lam,mu,precision=120)
        reverse=analytic_moments(a,D(f1),D(f0),lam,mu,precision=120)
        low=analytic_moments(a,D(f0),D(f1),lam,mu,precision=80)
        assert comparison([high["A0"],high["A1"]],[reverse["A0"],reverse["A0"]-reverse["A1"]],unit="N/mm^2",limit="1e-100")["status"]=="pass"
        assert comparison([low["A0"],low["A1"]],[high["A0"],high["A1"]],unit="N/mm^2")["status"]=="pass"


@pytest.mark.parametrize("bad",["0","-1","NaN"])
def test_nonpositive_or_nonfinite_stretch_rejected(bad):
    with pytest.raises(ValueError): analytic_moments(D(1),D(bad),D(1),D(2),D(3),precision=80)
