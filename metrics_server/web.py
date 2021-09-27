from typing import List, Literal, Optional, Tuple

import pkg_resources
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import settings
from .metrics import metrics_get, repo
from .session import Session, get_session

router = APIRouter(prefix='', default_response_class=HTMLResponse)

_data_path = pkg_resources.resource_filename(__package__, 'statics/')
_templates_path = pkg_resources.resource_filename(__package__, 'templates/')

templates = Jinja2Templates(directory=_templates_path)


def get_user(session: Session = Depends(get_session)) -> Optional[str]:
    if session.state == 'normal':
        return session.user
    return None


@router.get('/')
def web_index(request: Request, user: Optional[str] = Depends(get_user)):
    branches = list(repo.branches())
    base_url = get_base_url()
    return templates.TemplateResponse(
        'index.html', {
            'request': request,
            'title': 'Metrics',
            'user': user,
            'branches': branches,
            'base_url': base_url,
        })


@router.get('/results/{ref:path}')
def web_results_ref(request: Request,
                    ref: str,
                    user: Optional[str] = Depends(get_user)):
    branches = list(repo.branches())
    base_url = get_base_url()
    metrics_data = metrics_get(ref)
    metrics = metrics_data.metrics if metrics_data is not None else {}
    return templates.TemplateResponse(
        'results.html', {
            'request': request,
            'title': f'Metrics - {ref}',
            'user': user,
            'valid_ref': metrics_data is not None,
            'branches': branches,
            'base_url': base_url,
            'ref': ref,
            'metrics': metrics,
        })


@router.get('/compare/{ref:path}')
def web_compare_ref(request: Request,
                    ref: str,
                    user: Optional[str] = Depends(get_user),
                    to: List[str] = Query(...)):
    base_url = get_base_url()
    metrics_src = metrics_get(ref)
    metrics_dst = {to_ref: metrics_get(to_ref) for to_ref in to}
    metrics_dst = {k: v for k, v in metrics_dst.items() if v is not None}

    if metrics_src is None:
        return None

    def parse_name(
            name: str) -> Tuple[str, Literal['less', 'more', 'unknown']]:
        if name.startswith('+'):
            return name[1:], 'more'
        if name.startswith('-'):
            return name[1:], 'less'
        return name, 'unknown'

    # Get metric types
    metrics_types = {}
    for metric_name in metrics_src.metrics:
        name, order = parse_name(metric_name)
        metrics_types[name] = order
    for dst_data in metrics_dst.values():
        for metric_name in dst_data.metrics:
            name, _ = parse_name(metric_name)
            if name not in metrics_types:
                metrics_types[name] = 'unknown'

    # Normalize metric names
    metrics_src.metrics = {
        parse_name(name)[0]: value
        for name, value in metrics_src.metrics.items()
    }
    for dst_data in metrics_dst.values():
        dst_data.metrics = {
            parse_name(name)[0]: value
            for name, value in dst_data.metrics.items()
        }

    return templates.TemplateResponse(
        'compare.html', {
            'request': request,
            'title': 'Metrics comparison',
            'user': user,
            'base_url': base_url,
            'metrics_names': metrics_types,
            'main_ref': ref,
            'main_metrics': metrics_src,
            'to_metrics': metrics_dst,
        })


def get_base_url() -> str:
    base_url = settings.BASE_URL
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url


statics_app = StaticFiles(directory=_data_path)
