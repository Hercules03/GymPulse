import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../presentation/providers/chat_provider.dart';

class ChatBubbleWidget extends StatelessWidget {
  final String message;
  final bool isUser;
  final DateTime timestamp;
  final List<ChatRecommendation>? recommendations;

  const ChatBubbleWidget({
    super.key,
    required this.message,
    required this.isUser,
    required this.timestamp,
    this.recommendations,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!isUser) ...[
          CircleAvatar(
            radius: 16,
            backgroundColor: Theme.of(context).colorScheme.primary,
            child: const Icon(
              Icons.smart_toy,
              size: 16,
              color: Colors.white,
            ),
          ),
          const SizedBox(width: 8),
        ],
        Flexible(
          child: Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.75,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isUser 
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey[200],
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(20),
                topRight: const Radius.circular(20),
                bottomLeft: Radius.circular(isUser ? 20 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 20),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message,
                  style: TextStyle(
                    color: isUser ? Colors.white : Colors.black87,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _formatTime(timestamp),
                  style: TextStyle(
                    color: isUser ? Colors.white70 : Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
                // Show recommendations if available
                if (!isUser && recommendations != null && recommendations!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  ...recommendations!.map((rec) => _buildRecommendationCard(context, rec)),
                ],
              ],
            ),
          ),
        ),
        if (isUser) ...[
          const SizedBox(width: 8),
          CircleAvatar(
            radius: 16,
            backgroundColor: Colors.grey[300],
            child: const Icon(
              Icons.person,
              size: 16,
              color: Colors.grey,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildRecommendationCard(BuildContext context, ChatRecommendation recommendation) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue[200]!),
      ),
      child: InkWell(
        onTap: () => _handleRecommendationTap(context, recommendation),
        child: Row(
          children: [
            Icon(
              _getRecommendationIcon(recommendation.type),
              color: Colors.blue[700],
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recommendation.title,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.blue[900],
                      fontSize: 14,
                    ),
                  ),
                  if (recommendation.description.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      recommendation.description,
                      style: TextStyle(
                        color: Colors.blue[700],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios,
              color: Colors.blue[700],
              size: 16,
            ),
          ],
        ),
      ),
    );
  }

  IconData _getRecommendationIcon(String type) {
    switch (type) {
      case 'branch':
        return Icons.location_on;
      case 'machine':
        return Icons.fitness_center;
      case 'category':
        return Icons.category;
      default:
        return Icons.recommend;
    }
  }

  void _handleRecommendationTap(BuildContext context, ChatRecommendation recommendation) {
    if (recommendation.branchId != null) {
      // Navigate to branch details
      context.go('/branches');
      // TODO: Add specific branch navigation when implemented
    } else if (recommendation.machineId != null) {
      // Navigate to machine details
      context.go('/branches');
      // TODO: Add specific machine navigation when implemented
    } else if (recommendation.category != null) {
      // Navigate to category view
      context.go('/branches');
      // TODO: Add specific category navigation when implemented
    }
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${timestamp.day}/${timestamp.month}';
    }
  }
}
