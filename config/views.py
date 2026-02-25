import threading

from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.management import call_command
from django import db

from apps.carbone.constants import (
    FORETS_DATA, NOMENCLATURE_DATA, SUPERFICIE_TOTALE_HA,
    BIOMASSE_REFERENCE, CARBONE_TOTAL_REFERENCE, STOCK_CARBONE_REFERENCE,
)
from apps.carbone.models import OccupationSol


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forets'] = FORETS_DATA
        context['superficie_totale'] = SUPERFICIE_TOTALE_HA
        return context


class EnjeuxView(TemplateView):
    template_name = 'enjeux.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nomenclatures'] = NOMENCLATURE_DATA
        context['forets'] = FORETS_DATA
        context['superficie_totale'] = SUPERFICIE_TOTALE_HA
        # Only nomenclatures with non-zero carbon for the reference table
        context['nomenclatures_carbone'] = [
            n for n in NOMENCLATURE_DATA if n['stock_carbone_reference'] > 0
        ]
        return context


class CartesView(TemplateView):
    template_name = 'cartes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forets'] = FORETS_DATA
        return context


# ===== Import trigger (admin only) =====
_import_status = {'running': False, 'log': [], 'done': False}


def _run_import_background(url, only=None):
    """Run import in a background thread."""
    global _import_status
    _import_status = {'running': True, 'log': [], 'done': False}

    try:
        db.close_old_connections()
        import io

        class LogCapture(io.StringIO):
            def write(self, s):
                if s.strip():
                    _import_status['log'].append(s.strip())
                return super().write(s)

        log = LogCapture()
        kwargs = {'stdout': log}
        if only:
            kwargs['only'] = only

        call_command('import_from_url', url, **kwargs)
        _import_status['log'].append('ALL IMPORTS COMPLETE!')
    except Exception as e:
        _import_status['log'].append(f'ERROR: {e}')
    finally:
        _import_status['running'] = False
        _import_status['done'] = True


@staff_member_required
def trigger_import_view(request):
    """
    Admin-only endpoint to trigger data import.

    GET  /admin/trigger-import/          -> status
    POST /admin/trigger-import/          -> start import
    GET  /admin/trigger-import/?status=1 -> get progress
    """
    if request.method == 'POST' or request.GET.get('start'):
        if _import_status.get('running'):
            return JsonResponse({
                'status': 'already_running',
                'log': _import_status['log'][-20:],
            })

        url = request.POST.get(
            'url',
            request.GET.get(
                'url',
                'https://drive.google.com/file/d/1h11UM_rd35tsTtZWYsiV_J7LxL2JFJfG/view?usp=sharing'
            ),
        )
        only = request.POST.get('only', request.GET.get('only', 'occupations,cache'))

        thread = threading.Thread(
            target=_run_import_background,
            args=(url, only),
            daemon=True,
        )
        thread.start()

        return JsonResponse({
            'status': 'started',
            'message': f'Import started for: {only}',
            'check_progress': '/admin/trigger-import/?status=1',
        })

    if request.GET.get('status'):
        return JsonResponse({
            'running': _import_status.get('running', False),
            'done': _import_status.get('done', False),
            'log': _import_status.get('log', [])[-50:],
        })

    # Info page
    occ_count = OccupationSol.objects.count()
    return JsonResponse({
        'endpoint': 'Import Trigger',
        'occupations_in_db': occ_count,
        'instructions': {
            'start_occupations': '/admin/trigger-import/?start=1&only=occupations,cache',
            'start_all': '/admin/trigger-import/?start=1&only=nomenclature,forets,zones,occupations,placettes,infrastructure,cache',
            'check_progress': '/admin/trigger-import/?status=1',
        },
        'note': 'You must be logged in as admin (via /admin/) first.',
    })
