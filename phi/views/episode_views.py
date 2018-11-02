from backend import errors
from phi import models
from phi.response_serializers import EpisodeDetailsResponseSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import logging

logger = logging.getLogger(__name__)


class EpisodeView(APIView):
    queryset = models.Episode.objects.all()
    serializer_class = EpisodeDetailsResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'episodeIDs' in data:
            episode_list = data['episodeIDs']

            success_ids = list()
            failure_ids = list()
            for episode_id in episode_list:
                try:
                    episode = models.Episode.objects.filter(uuid=episode_id).get(is_active=True)
                    access = models.UserEpisodeAccess.objects.filter(user=user.profile).filter(episode=episode)
                    if access.exists():
                        success_ids.append(episode_id)
                    else:
                        failure_ids.append(episode_id)
                except Exception as e:
                    logger.error(str(e))
                    failure_ids.append(episode_id)
            return success_ids, failure_ids
        return None, None

    def get_objects_by_ids(self, ids):
        # These episodes exist and are active
        episodes = models.Episode.objects.filter(uuid__in=ids)
        return episodes

    def post(self, request):
        success_ids, failure_ids = self.get_results(request)
        success = self.get_objects_by_ids(success_ids)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = self.serializer_class(resp)
        return Response(serializer.data)
