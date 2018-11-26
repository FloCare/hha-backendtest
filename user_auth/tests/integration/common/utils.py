def compare_user(obj_instance, user_object, expected_hash):
    obj_instance.assertEqual(user_object.first_name, expected_hash['first_name'])
    obj_instance.assertEqual(user_object.last_name, expected_hash['last_name'])
    obj_instance.assertEqual(user_object.email, expected_hash['email'])
    obj_instance.assertEqual(user_object.username, expected_hash['email'])


def compare_user_profile(obj_instance, user_object, expected_hash):
    obj_instance.assertEqual(user_object.contact_no, expected_hash['contact_no'])