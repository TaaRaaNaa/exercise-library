import json

from django.http import Http404
from django.http import HttpResponse
from exercise_library.auto_corrector import SpellChecker, AutoCompleter
from exercise_library.exercise_cacher import ExerciseCacher
from exercise_library.cloud_search.tasks import save_exercise_to_amazon

from exercise_library.constants import Equipment
from exercise_library.constants import ExerciseType
from exercise_library.constants import MuscleGroup
from exercise_library.constants import Phase
from exercise_library.constants import WorkoutComponent


def render_to_json(response_obj, context={}, content_type="application/json", status=200):
    json_str = json.dumps(response_obj, indent=4)
    return HttpResponse(json_str, content_type=content_type, status=status)


def requires_post(fn):
    def inner(request, *args, **kwargs):
        if request.method != "POST":
            return Http404
        post_data = request.POST or json.loads(request.body)
        kwargs["post_data"] = post_data
        return fn(request, *args, **kwargs)
    return inner


def get_exercises(request):
    return render_to_json({
        'exercises': ExerciseCacher().exercises,
        'equipment': sorted(Equipment.as_json(), key=lambda d: d['title']),
        'muscle_groups': sorted(MuscleGroup.as_json(), key=lambda d: d['title']),
        'phases': sorted(Phase.as_json(), key=lambda p: p['title']),
        'workout_components': sorted(WorkoutComponent.as_json(), key=lambda w: w['title']),
        'exercise_types': sorted(ExerciseType.as_json(), key=lambda d: d['title'])
    })


def autocomplete(request):
    spellchecker = SpellChecker()
    search_term_so_far = request.GET.get('q', '')

    tokens = spellchecker.correct_phrase(search_term_so_far)
    suggestions = AutoCompleter().guess_exercises(tokens)

    return render_to_json(suggestions)


@requires_post
def save_exercise(request, post_data=None):
    post_data = post_data or {}
    save_exercise_to_amazon(post_data)
    return render_to_json({}, status=204)


def exercise_from_name(request):
    exercise_name = request.GET.get('exercise', '')
    exercise_dict = AutoCompleter().get_exercise_dict_from_name(exercise_name)
    return render_to_json(exercise_dict)
