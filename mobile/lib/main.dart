import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'app/app.dart';
import 'core/config/environment_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize environment configuration
  await EnvironmentConfig.initialize();
  
  // Initialize Hive for local storage
  await Hive.initFlutter();
  
  runApp(const AppInitializer(
    child: GymPulseApp(),
  ));
}