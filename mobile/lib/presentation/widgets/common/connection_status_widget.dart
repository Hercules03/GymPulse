import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/services/websocket_service.dart';
import '../../providers/gym_provider.dart';

class ConnectionStatusWidget extends StatelessWidget {
  final bool showLabel;
  final double iconSize;

  const ConnectionStatusWidget({
    super.key,
    this.showLabel = true,
    this.iconSize = 16,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        final state = gymProvider.webSocketState;
        final isConnected = gymProvider.isWebSocketConnected;

        Color iconColor;
        IconData icon;
        String label;

        switch (state) {
          case WebSocketConnectionState.connected:
            iconColor = Colors.green;
            icon = Icons.wifi;
            label = 'Live';
            break;
          case WebSocketConnectionState.connecting:
          case WebSocketConnectionState.reconnecting:
            iconColor = Colors.orange;
            icon = Icons.wifi_tethering;
            label = 'Connecting...';
            break;
          case WebSocketConnectionState.error:
            iconColor = Colors.red;
            icon = Icons.wifi_off;
            label = 'Connection error';
            break;
          case WebSocketConnectionState.disconnected:
          default:
            iconColor = Colors.grey;
            icon = Icons.wifi_off;
            label = 'Offline';
            break;
        }

        if (!showLabel) {
          return Icon(
            icon,
            color: iconColor,
            size: iconSize,
          );
        }

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: iconColor,
              size: iconSize,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: iconColor,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        );
      },
    );
  }
}

class ConnectionStatusBanner extends StatelessWidget {
  const ConnectionStatusBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        final state = gymProvider.webSocketState;

        // Only show banner for error states
        if (state != WebSocketConnectionState.error) {
          return const SizedBox.shrink();
        }

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 8,
          ),
          color: Colors.red[100],
          child: Row(
            children: [
              Icon(
                Icons.wifi_off,
                color: Colors.red[700],
                size: 16,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Connection lost. Real-time updates are not available.',
                  style: TextStyle(
                    color: Colors.red[700],
                    fontSize: 12,
                  ),
                ),
              ),
              TextButton(
                onPressed: () {
                  gymProvider.connectWebSocket();
                },
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: const Size(0, 32),
                ),
                child: Text(
                  'Retry',
                  style: TextStyle(
                    color: Colors.red[700],
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class RealTimeIndicator extends StatefulWidget {
  final Widget child;

  const RealTimeIndicator({
    super.key,
    required this.child,
  });

  @override
  State<RealTimeIndicator> createState() => _RealTimeIndicatorState();
}

class _RealTimeIndicatorState extends State<RealTimeIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(seconds: 1),
      vsync: this,
    )..repeat(reverse: true);

    _animation = Tween<double>(
      begin: 0.5,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        final isConnected = gymProvider.isWebSocketConnected;

        if (!isConnected) {
          return widget.child;
        }

        return Stack(
          children: [
            widget.child,
            Positioned(
              top: 8,
              right: 8,
              child: AnimatedBuilder(
                animation: _animation,
                builder: (context, child) {
                  return Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(_animation.value),
                      shape: BoxShape.circle,
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
    );
  }
}