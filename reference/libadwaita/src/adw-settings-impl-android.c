/*
 * Copyright (c) 2025 Florian "sp1rit" <sp1rit@disroot.org>
 *
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Author: Florian "sp1rit" <sp1rit@disroot.org>
 */

#include "config.h"

#include "adw-settings-impl-private.h"

#include <gdk/android/gdkandroid.h>

struct _AdwSettingsImplAndroid
{
  AdwSettingsImpl parent_instance;

  GdkDisplay *display;
};

G_DEFINE_FINAL_TYPE (AdwSettingsImplAndroid, adw_settings_impl_android, ADW_TYPE_SETTINGS_IMPL)

static void
update_color_scheme (AdwSettingsImplAndroid *self)
{
  GdkAndroidDisplayNightMode night_mode =
    gdk_android_display_get_night_mode (GDK_ANDROID_DISPLAY (self->display));

  switch (night_mode) {
  case GDK_ANDROID_DISPLAY_NIGHT_UNDEFINED:
    adw_settings_impl_set_features (ADW_SETTINGS_IMPL (self),
                                    FALSE,
                                    adw_settings_impl_get_has_high_contrast (ADW_SETTINGS_IMPL (self)),
                                    adw_settings_impl_get_has_accent_colors (ADW_SETTINGS_IMPL (self)),
                                    adw_settings_impl_get_has_document_font_name (ADW_SETTINGS_IMPL (self)),
                                    adw_settings_impl_get_has_monospace_font_name (ADW_SETTINGS_IMPL (self)));
    break;
  case GDK_ANDROID_DISPLAY_NIGHT_NO:
    adw_settings_impl_set_color_scheme (ADW_SETTINGS_IMPL (self),
                                        ADW_SYSTEM_COLOR_SCHEME_DEFAULT);
    break;
  case GDK_ANDROID_DISPLAY_NIGHT_YES:
    adw_settings_impl_set_color_scheme (ADW_SETTINGS_IMPL (self),
                                        ADW_SYSTEM_COLOR_SCHEME_PREFER_DARK);
    break;
  default:
    g_assert_not_reached ();
  }
}

static void
update_accent_color (AdwSettingsImplAndroid *self)
{
  const GdkRGBA *accent_color = gdk_android_display_get_accent_color (GDK_ANDROID_DISPLAY (self->display));
  adw_settings_impl_set_accent_color (ADW_SETTINGS_IMPL (self),
                                      adw_accent_color_nearest_from_rgba (accent_color));
}

static void
adw_settings_impl_android_constructed (GObject *object)
{
  AdwSettingsImplAndroid *self = ADW_SETTINGS_IMPL_ANDROID (object);
  GdkDisplay *display = gdk_display_get_default ();

  if (GDK_IS_ANDROID_DISPLAY (display)) {
    self->display = display;
    g_object_add_weak_pointer (G_OBJECT (self->display), (gpointer *) &self->display);

    adw_settings_impl_set_features (ADW_SETTINGS_IMPL (self),
                                    TRUE, FALSE, TRUE, FALSE, FALSE);

    g_signal_connect_swapped (self->display, "notify::accent-color",
                              G_CALLBACK (update_accent_color), self);
    update_accent_color (self);

    g_signal_connect_swapped (self->display, "notify::night-mode",
                              G_CALLBACK (update_color_scheme), self);
    update_color_scheme (self);
  }

  G_OBJECT_CLASS (adw_settings_impl_android_parent_class)->constructed (object);
}

static void
adw_settings_impl_android_dispose (GObject *object)
{
  AdwSettingsImplAndroid *self = ADW_SETTINGS_IMPL_ANDROID (object);

  if (self->display) {
    g_signal_handlers_disconnect_by_func (self->display, update_color_scheme, self);
    g_object_remove_weak_pointer (G_OBJECT (self->display), (gpointer *)&self->display);
  }

  G_OBJECT_CLASS (adw_settings_impl_android_parent_class)->dispose (object);
}

static void
adw_settings_impl_android_class_init (AdwSettingsImplAndroidClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->constructed = adw_settings_impl_android_constructed;
  object_class->dispose = adw_settings_impl_android_dispose;
}

static void
adw_settings_impl_android_init (AdwSettingsImplAndroid *self)
{
}

AdwSettingsImpl *
adw_settings_impl_android_new (gboolean enable_color_scheme,
                               gboolean enable_high_contrast,
                               gboolean enable_accent_colors,
                               gboolean enable_document_font_name,
                               gboolean enable_monospace_font_name)
{
  AdwSettingsImpl *self = g_object_new (ADW_TYPE_SETTINGS_IMPL_ANDROID, NULL);

  adw_settings_impl_set_features (self,
                                  enable_color_scheme,
                                  FALSE,
                                  enable_accent_colors,
                                  FALSE,
                                  FALSE);

  return self;
}
