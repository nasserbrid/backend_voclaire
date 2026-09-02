"""Base de connaissance du chatbot d'onboarding.

Contenu injecté en entier dans le system prompt (pas de RAG en v1) — voir
chat_service.build_system_prompt(). Prose uniquement, pas de Markdown ni de
listes à puces techniques : le texte est lu par le LLM, pas rendu à l'écran.

Fichier .py (pas .md) car .dockerignore exclut *.md — un .md ne serait pas
présent dans l'image Docker construite en prod.
"""

KB_TEXT: str = """
Transcription (Whisper)
Voclaire transcrit des fichiers audio ou vidéo en texte grâce à Whisper (modèle de reconnaissance vocale).
Les formats audio courants sont acceptés (mp3, wav, m4a, webm, ogg...).
En plan Free, chaque transcription (fichier ou enregistrement) est limitée à 2 heures maximum, et l'utilisateur dispose de deux quotas mensuels distincts : jusqu'à 4 heures de fichiers audio importés par mois, et jusqu'à 4 heures d'enregistrements de réunion par mois. Ces deux quotas ne se partagent pas : un utilisateur peut utiliser ses 4 heures de fichiers ET ses 4 heures de réunions dans le même mois.
En plan Pro, la transcription est illimitée en volume mensuel. Les fichiers importés peuvent aller jusqu'à 3 heures.

Correction, reformulation et résumé (post-traitement LLM)
Une fois une transcription obtenue, l'utilisateur peut demander un post-traitement par intelligence artificielle en un clic, avec plusieurs modes possibles : correction des tournures orales et des hésitations, reformulation dans un style plus clair, ou résumé condensé du contenu.
En plan Free, ce post-traitement est limité à 10 utilisations par mois, tous modes confondus.
En plan Pro, ce post-traitement est illimité.

Diarisation, c'est-à-dire identifier qui a parlé
Pour les enregistrements avec plusieurs personnes (réunions), Voclaire peut séparer automatiquement la transcription par intervenant, pour savoir qui a dit quoi et à quel moment.
Les intervenants sont identifiés par des labels génériques : "Intervenant 1", "Intervenant 2", "Intervenant 3", etc. Voclaire n'affiche jamais de prénom réel ni de nom identifié automatiquement — seulement des numéros d'intervenant, dans l'ordre d'apparition dans la conversation.
Cette fonctionnalité est disponible à la même qualité sur le plan Free et sur le plan Pro : elle n'est jamais réservée au payant.

Dictaphone de réunion (enregistrement direct)
Voclaire permet d'enregistrer une réunion en cours directement depuis le navigateur (Google Meet, Teams, Zoom...), en capturant l'audio de l'onglet partagé — pas seulement le micro de l'utilisateur, donc tous les participants sont captés même s'ils portent un casque.
La démo publique accessible sans compte sur la page d'accueil permet d'enregistrer jusqu'à 10 minutes maximum.
En plan Free (avec compte), l'enregistrement de réunion est limité à 4 heures par mois au total, dans la limite de 2 heures par enregistrement.
En plan Pro, un enregistrement individuel peut aller jusqu'à 30 minutes, sans limite mensuelle de volume.

Export des documents
Une fois la transcription obtenue (et éventuellement post-traitée), elle peut être exportée en fichier téléchargeable.
En plan Free, seul l'export au format DOCX (Word) brut est disponible, structuré par tour de parole quand la diarisation est présente.
En plan Pro, trois formats structurés sont disponibles : DOCX, PDF et PPTX (PowerPoint), avec une mise en forme travaillée (titres, sections, résumé, actions) plutôt qu'un texte brut.

Comptes et connexion
La création de compte se fait par email et mot de passe, ou en un clic via Google (connexion Google OAuth). Aucune carte bancaire n'est demandée pour créer un compte gratuit ni pour utiliser le plan Free.
La démo sur la page d'accueil ne nécessite aucun compte : elle est limitée à 10 minutes d'enregistrement et ne conserve rien après la session.

Confidentialité et RGPD
Les données (audio et transcriptions) des utilisateurs de Voclaire sont hébergées en Union européenne. Voclaire respecte le RGPD.
La démo publique sans compte ne conserve aucune donnée après la transcription affichée.

Limites générales
Plan Free : 4h de fichiers audio par mois, 4h d'enregistrements de réunion par mois, 2h maximum par élément transcrit, 10 post-traitements LLM par mois, export DOCX brut uniquement, sans carte bancaire.
Plan Pro : transcription illimitée (fichiers jusqu'à 3h chacun), enregistrement de réunion jusqu'à 30 minutes par session, post-traitement LLM illimité, exports DOCX/PDF/PPTX structurés.
Démo publique sans compte : 10 minutes maximum, aucune sauvegarde.

Passage en plan Pro
Le plan Pro coûte 9,99 € par mois en facturation mensuelle, ou 7,99 € par mois en facturation annuelle (soit 95,88 € par an, facturés en une fois).
Le passage en Pro se fait depuis la page des tarifs ou depuis l'application, via un paiement sécurisé par carte bancaire (Stripe). L'abonnement peut être résilié à tout moment depuis l'espace de gestion de l'abonnement ("portail client"), la résiliation prenant effet à la fin de la période déjà payée.
""".strip()
